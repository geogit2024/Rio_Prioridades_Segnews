import csv
from pathlib import Path

import requests

BASE_URL = "http://www.ispdados.rj.gov.br/Arquivos"
DATA_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

DATASETS = {
    "dp_evolucao_mensal_cisp": "BaseDPEvolucaoMensalCisp.csv",
    "municipio_mensal": "BaseMunicipioMensal.csv",
    "municipio_taxa_mes": "BaseMunicipioTaxaMes.csv",
    "municipio_taxa_ano": "BaseMunicipioTaxaAno.csv",
}


def download_dataset(name):
    filename = DATASETS[name]
    resp = requests.get(f"{BASE_URL}/{filename}", timeout=60)
    resp.raise_for_status()
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_RAW_DIR / filename
    out_path.write_bytes(resp.content)
    return out_path


def filter_csv_by_cisp(csv_path, cisp_codes, out_path):
    cisp_codes = {str(c) for c in cisp_codes}
    with open(csv_path, encoding="latin-1", newline="") as f_in:
        reader = csv.DictReader(f_in, delimiter=";")
        rows = [row for row in reader if row["cisp"] in cisp_codes]
        fieldnames = reader.fieldnames

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
