# ============================================
# GPX → 平面直交座標系9系 CSV変換スクリプト
# Version: 1.2.0
#
# 概要:
#   GPX（WGS84）で記録されたwaypointを読み込み，
#   日本平面直交座標系第9系（EPSG:6677）へ変換し，
#   CSV形式（CODE,X,Y,Z,ANTENNA_HEIGHT,DATE）で出力する。
#
# 依存ライブラリ:
#   pyproj
#
# ============================================
# 変更履歴:
# --------------------------------------------
# v1.2.0 (2026-03-20)
#   - アンテナ高をCSV第5カラムとして出力
#   - DATEカラムを第6カラムへ移動
#
# v1.1.0 (2026-03-20)
#   - アンテナ高引数を追加
#   - Z値を <ele> - アンテナ高 に変更（Alt値）
#
# v1.0.0 (2026-03-20)
#   - 初版作成
# --------------------------------------------
# ============================================

import xml.etree.ElementTree as ET
import csv
import argparse
import os
from pyproj import Transformer
from datetime import datetime


def convert_gpx_to_csv(input_gpx, output_dir, antenna_height):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6677", always_xy=True)

    tree = ET.parse(input_gpx)
    root = tree.getroot()

    # 名前空間対応
    if root.tag.startswith("{"):
        ns_uri = root.tag.split("}")[0].strip("{")
        ns = {"gpx": ns_uri}
        wpt_path = "gpx:wpt"
        ele_path = "gpx:ele"
        name_path = "gpx:name"
        time_path = "gpx:time"
    else:
        ns = {}
        wpt_path = "wpt"
        ele_path = "ele"
        name_path = "name"
        time_path = "time"

    rows = []

    for i, wpt in enumerate(root.findall(wpt_path, ns)):
        try:
            lat = float(wpt.get("lat"))
            lon = float(wpt.get("lon"))
        except (TypeError, ValueError):
            continue

        ele = wpt.find(ele_path, ns)
        name = wpt.find(name_path, ns)
        time_elem = wpt.find(time_path, ns)

        # 元高さ
        try:
            raw_z = float(ele.text) if ele is not None else 0.0
        except:
            raw_z = 0.0

        # アンテナ高補正
        z = raw_z - antenna_height

        # 測点名
        if name is not None and name.text:
            name_text = name.text
        else:
            name_text = f"P{i+1:03d}"

        # 観測日
        date_str = ""
        if time_elem is not None and time_elem.text:
            try:
                dt = datetime.fromisoformat(time_elem.text.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y%m%d")
            except:
                date_str = ""

        x, y = transformer.transform(lon, lat)

        rows.append([name_text, x, y, z, antenna_height, date_str])

    # 出力ファイル名
    base_name = os.path.splitext(os.path.basename(input_gpx))[0]
    output_csv = os.path.join(output_dir, base_name + ".csv")

    # CSV書き出し
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["CODE", "X", "Y", "Z", "ANTENNA_HEIGHT", "DATE"])
        writer.writerows(rows)

    return output_csv


def main():
    parser = argparse.ArgumentParser(description="GPX → 平面直交座標系9系CSV変換")
    parser.add_argument("input_gpx", help="入力GPXファイル")
    parser.add_argument("output_dir", help="出力ディレクトリ")
    parser.add_argument("antenna_height", type=float, help="アンテナ高（m）")
    args = parser.parse_args()

    output_csv = convert_gpx_to_csv(
        args.input_gpx,
        args.output_dir,
        args.antenna_height
    )

    print(f"変換完了: {output_csv}")


if __name__ == "__main__":
    main()