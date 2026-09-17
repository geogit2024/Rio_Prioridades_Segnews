from pathlib import Path

from src.scrapers.isp import DATA_PROCESSED_DIR, download_dataset, filter_csv_by_cisp
from src.utils.geo import find_intersecting, load_named_polygons, load_polygons_from_kmz

AOI_PATH = Path(__file__).resolve().parents[2] / "Regiao_interesse_NT.KMZ"
CISP_PATH = Path(__file__).resolve().parents[2] / "data" / "CISP_limites.kmz"


def matching_cisp_codes():
    _, aoi_polygon = load_polygons_from_kmz(AOI_PATH)[0]
    cisps = load_named_polygons(CISP_PATH)
    return [name for name, _ in find_intersecting(cisps, aoi_polygon)]


def main():
    cisp_codes = matching_cisp_codes()
    print(f"CISPs que cruzam a região de interesse: {sorted(cisp_codes, key=int)}")

    raw_path = download_dataset("dp_evolucao_mensal_cisp")
    out_path = DATA_PROCESSED_DIR / "isp_dp_evolucao_mensal_nova_terra_aoi.csv"
    count = filter_csv_by_cisp(raw_path, cisp_codes, out_path)
    print(f"Linhas filtradas: {count}")
    print(f"Salvo em: {out_path}")


if __name__ == "__main__":
    main()
