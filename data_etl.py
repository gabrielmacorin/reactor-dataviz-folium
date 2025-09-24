import pandas as pd
import numpy as np
import geopandas as gpd
import unicodedata

from tqdm import tqdm
from glob import glob
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from utils import constants


def load_data(input_pattern="data/external/*.xlsx"):
    """
    Carrega, processa e consolida dados de múltiplos arquivos e planilhas Excel.

    Args:
        str: Padrão de busca para os arquivos Excel de entrada.
    """
    print("Iniciando o carregamento dos dados...")

    excel_files = glob(input_pattern)
    if not excel_files:
        print(f"\nNenhum arquivo encontrado com o padrão: {input_pattern}")
        return


    processed_sheets = []
    for file_path in excel_files:
        try:
            excel_file = pd.ExcelFile(file_path)
            valid_sheets = [s for s in excel_file.sheet_names 
                              if s.upper() not in constants.excluded_sheets]

            for sheet_name in valid_sheets:
                keyword = next((kw for kw in constants.sheet_config 
                                   if kw in sheet_name.upper()), None)

                if not keyword:
                    print(f"\nIgnorando planilha: '{sheet_name}' no arquivo '{file_path}' (tipo não mapeado).")
                    continue

                print(f"\nProcessando arquivo: '{file_path}', planilha: '{sheet_name}'")
                df_sheet = excel_file.parse(sheet_name)
                
                tipo, descr_col = constants.sheet_config[keyword]
                df_sheet["TIPO"] = tipo
                df_sheet["DESCR_TIPO"] = df_sheet[descr_col]
                
                processed_sheets.append(df_sheet)

        except Exception as e:
            print(f"\nErro ao processar o arquivo '{file_path}': {e}")
            continue

    if not processed_sheets:
        print("Nenhuma planilha válida foi processada. Saindo.")
        return

    df = pd.concat(processed_sheets, ignore_index=True)

    return df


def prepare_data(data, start_date, end_date):
    """
    Prepara e limpa os dados de ocorrências, aplicando agregações, normalizações e filtros.

    Args:
        data (pd.DataFrame): O DataFrame bruto de entrada.
        start_date (str): A data de início do filtro (formato 'YYYY-MM-DD').
        end_date (str): A data de fim do filtro (formato 'YYYY-MM-DD').

    Returns:
        pd.DataFrame: O DataFrame processado e pronto para análise.
    """
    grouping_keys = ["NOME_DELEGACIA", "ANO_BO", "NUM_BO", "TIPO", "DESCR_TIPO"]
    agg_cols = {
        "DATA_OCORRENCIA_BO": "first", "CIDADE": "first", "BAIRRO": "first",
        "LOGRADOURO": "first", "NUMERO_LOGRADOURO": "first", "DESCR_MARCA_VEICULO": "first",
        "DESCR_OCORRENCIA_VEICULO": "first", "LATITUDE": "first", "LONGITUDE": "first"
    }

    df = data.groupby(grouping_keys, as_index=False).agg(agg_cols)
    df.columns = df.columns.str.lower()

    df = df[(df["data_ocorrencia_bo"] >= start_date) & (df["data_ocorrencia_bo"] <= end_date)]

    df.loc[df["latitude"] == 0, "latitude"] = None
    df.loc[df["longitude"] == 0, "longitude"] = None

    df["numero_logradouro"] = (
        df["numero_logradouro"].fillna(-99)
                               .astype(int)
                               .replace(-99, "S/N")
    )

    df["norm_cidade"] = df["cidade"].apply(normalize_text)
    df["norm_cidade"] = df["norm_cidade"].str.replace("S.", "SAO ")
    df['norm_cidade'] = df['norm_cidade'].replace(constants.adjusted_region_names)

    logradouro_str = df['logradouro'].astype(str)
    numero_str     = df['numero_logradouro'].astype(str)
    bairro_str     = df['bairro'].astype(str)
    cidade_str     = df['norm_cidade'].astype(str)

    df["endereco_completo"] = (
        logradouro_str + ", " +
        numero_str + ", " +
        bairro_str + ", " +
        cidade_str + " - SP"
    )

    df["endereco_completo"] = df["endereco_completo"].str.replace("VEDAÇÃO DA DIVULGAÇÃO DOS DADOS RELATIVOS,", "", regex=False)
    df["endereco_completo"] = df["endereco_completo"].str.replace("S/N,", "", regex=False)
    df[["latitude", "longitude"]] = df[["latitude", "longitude"]].replace(0, np.nan)

    return df


def get_population_estimate(df):
    """
    Carrega dados de estimativa populacional e os adiciona a um DataFrame existente.

    Args:
        df (pd.DataFrame): O DataFrame principal ao qual os dados de população serão adicionados.
                          Deve conter uma coluna 'norm_cidade'.
    Returns:
        pd.DataFrame: O DataFrame original com a coluna 'populacao_estimada' adicionada.
    """
    estimativa_populacional = pd.read_excel("data/external/estimativa_dou_2025.xls", 
                                            sheet_name="Municípios", 
                                            dtype={"COD. MUNIC": str},
                                            skiprows=1)
    estimativa_populacional = estimativa_populacional.dropna()

    estimativa_populacional["norm_cidade"] = estimativa_populacional["NOME DO MUNICÍPIO"].apply(normalize_text)
    estimativa_populacional = estimativa_populacional[estimativa_populacional["UF"] == "SP"]
    estimativa_populacional = estimativa_populacional.rename(columns={"POPULAÇÃO ESTIMADA": "populacao_estimada",
                                                                    "COD. MUNIC": "cod_municipio"})
    
    estimativa_populacional = df.merge(estimativa_populacional[["cod_municipio", "norm_cidade", "populacao_estimada"]], 
                                       on="norm_cidade", 
                                       how="left")
    
    # Mantém apenas os municípios de SP
    estimativa_populacional = estimativa_populacional.dropna(subset=["cod_municipio"])
    
    return estimativa_populacional


def save_shapefile_sp(input_path="data/external/shape_sp/SP_Municipios_2024.shp",
                      output_path="data/processed/SP_Municipios_2024.geojson"):
    """
    Lê um shapefile de municípios, filtra para o estado de São Paulo (SP),
    ajusta o código do município e salva o resultado como um GeoJSON.

    Args:
        input_path (str): O caminho para o shapefile de entrada.
        output_path (str): O caminho para o arquivo GeoJSON de saída.

    Returns:
        gpd.GeoDataFrame: O GeoDataFrame processado.
    """
    geo_sp = gpd.read_file(input_path)

    geo_sp = geo_sp[geo_sp["CD_UF"] == "35"]
    geo_sp["CD_MUN"] = geo_sp["CD_MUN"].astype(str).str[2:]

    geo_sp.to_file(output_path, driver="GeoJSON")

    return geo_sp


def get_geolocation(df):
    """
    Preenche coordenadas de latitude e longitude ausentes em um DataFrame.

    A função identifica endereços únicos sem coordenadas, busca-os usando a API do Nominatim
    de forma otimizada (sem duplicatas e com limite de requisições), e atualiza o DataFrame original.

    Args:
        df (pd.DataFrame): DataFrame contendo as colunas 'endereco_completo', 'latitude' e 'longitude'.

    Returns:
        pd.DataFrame: O DataFrame com as coordenadas preenchidas.
    """
    
    geolocator = Nominatim(user_agent="app_v1", timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, return_value_on_exception=None)

    tqdm.pandas(desc="Geocodificando endereços")

    nodup_location = (
        df.drop_duplicates(subset=["endereco_completo"])
        .loc[lambda df: df["latitude"].isna() | df["longitude"].isna()]
    )

    nodup_location = (
        nodup_location
        .assign(geo_coord=nodup_location["endereco_completo"].progress_apply(geocode))
        .assign(
            latitude_coord=lambda df: df["geo_coord"].apply(lambda loc: getattr(loc, "latitude", None)),
            longitude_coord=lambda df: df["geo_coord"].apply(lambda loc: getattr(loc, "longitude", None))
        )
        [["endereco_completo", "latitude_coord", "longitude_coord"]]
    )

    locations = (
        df
        .merge(nodup_location, on="endereco_completo", how="left")
        .assign(
            latitude=lambda df: df["latitude"].fillna(df["latitude_coord"]),
            longitude=lambda df: df["longitude"].fillna(df["longitude_coord"])
        )
        .drop(columns=["latitude_coord", "longitude_coord"])
    )

    return locations


def normalize_text(text):
    """Normaliza uma única string.

    - Remove acentos e caracteres especiais.
    - Converte para maiúsculas.
    - Normaliza espaços em branco (remove excessos no início, meio e fim).
    - Retorna uma string vazia se a entrada for nula ou vazia.

    Args:
        text: A string a ser normalizada.

    Returns:
        str: A string normalizada.
    """
    if not isinstance(text, str) or not text:
        return ""

    normalized_text = (
        unicodedata.normalize("NFKD", text)
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .upper()
    )

    return " ".join(normalized_text.split())


if __name__ == "__main__":
    print("Iniciando o processo de ETL...\n")
    df = load_data()

    print("\nPreparando os dados...")
    df = prepare_data(df, "2025-01-01", "2025-06-30")

    print("\nAdicionando estimativas populacionais...")
    df = get_population_estimate(df)

    print("\nSalvando shapefile de SP...")
    geo_sp = save_shapefile_sp()
    df = df.merge(geo_sp[["CD_MUN", "AREA_KM2"]].rename(columns={"CD_MUN": "cod_municipio", "AREA_KM2": "area_km2"}), 
                  on="cod_municipio", 
                  how="left")
    
    # df.to_csv("data/raw/ocorrencias_2025_1sem.csv", index=False)

    print("\nPreenchendo geolocalizações ausentes...")
    df = get_geolocation(df)

    print(f"Dados processados com sucesso. Período: {df['data_ocorrencia_bo'].min()} a {df['data_ocorrencia_bo'].max()}")
    print(f"Número total de registros: {len(df)}")
    print(f"Proporção de nulos:\n{df.isnull().sum() / len(df)}")

    df[constants.needed_columns].to_csv("data/processed/ocorrencias_2025_1sem.csv", index=False)