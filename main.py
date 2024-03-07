import argparse
import httpx
import itertools
import asyncio
import os


async def fetch_desa(kode, client):
    print(
        f"Fetch: https://sirekap-obj-data.kpu.go.id/pemilu/hhcw/pdprdp/33/{kode[0]}/{kode[1]}/{kode[2]}.json"
    )
    response = await client.get(
        f"https://sirekap-obj-data.kpu.go.id/pemilu/hhcw/pdprdp/33/{kode[0]}/{kode[1]}/{kode[2]}.json",
        headers={"Referer": "https://pemilu2024.kpu.go.id/"},
    )
    j_resp = response.json()

    return j_resp


async def fetch_all_desa(kode):
    async with httpx.AsyncClient(timeout=60) as client:
        return await asyncio.gather(
            *map(
                fetch_desa,
                kode,
                itertools.repeat(client),
            )
        )


def generate_payload(kabupaten):
    # Generate array of kode payload
    # kode = [kab_kode, kec_kode, desa_kode]
    # info = [kecamatan, desa]

    kode = []
    info = []
    with open(f"source/{kabupaten}.csv", "r") as f:
        for line in f:
            kec_kode, kec_name = line[:-1].split(";")

            with open(f"source/{kabupaten}/{kec_kode}.csv", "r") as d:
                for line in d:
                    desa_kode, desa_name = line[:-1].split(";")

                    kode.append([kec_kode[0:4], kec_kode, desa_kode])
                    info.append([kec_name, desa_name])

    return kode, info


def parse_tps(kode, info, table):
    row_str = ""
    for key in table.keys():
        row_str += f"{info[0]};{info[1]};TPS-{key[-3:]};"

        if len(table[key]) > 3:
            row_str += f"{';'.join(list(map(str, list(table[key].values())[:-3])))}\n"
            continue

        row_str += f"Data sedang diproses lihat C1 di: https://pemilu2024.kpu.go.id/pilegdprd_prov/hitung-suara/wilayah/33/{kode[0]}/{kode[1]}/{kode[2]}/{key}\n"

    return row_str


def data_kab(kabupaten, output_path):
    kode, info = generate_payload(kabupaten)

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(fetch_all_desa(kode))

    with open(f"{output_path}/{kabupaten}.csv", "w") as f:
        f.write(
            "Kecamatan;Desa/Kelurahan;TPS;1 PKB;2 Gerindra;3 PDIP;4 Golkar;5 Nasdem;6 Buruh;7 Gelora;8 PKS;9 PKN;10 Hanura;11 Garuda;12 PAN;13 PBB;14 Demokrat;15 PSI;16 Perindo;17 PPP;24 Umat\n"
        )
        for i in range(len(kode)):
            f.write(parse_tps(kode[i], info[i], result[i]["table"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gather Data from sirekap kpu")
    parser.add_argument(
        "--output",
        help="Folder output for csv file (default: result).",
        default="result",
    )

    args = parser.parse_args()

    output_path = args.output

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    kabupaten = ["banyumas", "cilacap"]
    for k in kabupaten:
        data_kab(k, output_path)
