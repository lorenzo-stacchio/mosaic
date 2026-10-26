import urllib.request
import pandas as pd
import os
import argparse
import json 

def checkdircreate(path):
    if not os.path.exists(path):
        os.mkdir(path)


def download_url(url, path):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    folder_path = path  # f"outs/temp.csv"
    # urllib.request.urlretrieve(url, folder_path)
    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req) as response:
        with open(folder_path, "wb") as f:
            f.write(response.read())


def dataframe_update(temp_df, filter_area, filter_subareas):
    # Filter by area
    temp_df = temp_df[temp_df["Areas"].str.contains(filter_area)]
    # Filter by category
    for cat in filter_subareas:
        temp_df = temp_df[temp_df["Categories"].str.contains(cat)]

    return temp_df
    # temp_df.to_csv(f"{subfolder_path}{filter_area}_{contribution_name}.csv", index=False)
    # temp_df.to_excel(f"{subfolder_path}{filter_area}_{contribution_name}.xlsx", index=False)


pivot_area_code = "1700"  # computer science
pivot_sub_area_code = None  # eletrical and electronic engineering


def parse_arguments():
    parser = argparse.ArgumentParser(description="A script that demonstrates argparse.")
    # Add arguments
    parser.add_argument(
        "-c", "--config", 
        type=str, 
        help="The path to the config json", 
        required=True
    )
    parser.add_argument(
        "-sub", "--sub_area_computer_science_code", 
        type=int, 
        help="Numerical Code from scimago for the subarea of computer science (Artificial Intelligence is 1702)", 
    )
    
    # Parse the arguments
    args = parser.parse_args()
    return args
    

if __name__ == "__main__":
    args = parse_arguments()
    filter_area = json.load(open(args.config)) #{"Medicine":["Orthopedics and Sports Medicine"]}

    mode = "aggregative" # or cascade filter

    # mode = "cascade" # or cascade filter
    list_types = ["all"]

    path_csv_temp = f"outs/temp.csv"
    for contr_type in list_types:
        # if pivot_sub_area_code:
        #     # https://www.scimagojr.com/journalrank.php?area=1700&out=xls
        #     url_temp = f"https://www.scimagojr.com/journalrank.php?area={pivot_area_code}&category={pivot_sub_area_code}&type={contr_type}&out=xls"
        # else:
        #     url_temp = f"https://www.scimagojr.com/journalrank.php?area={pivot_area_code}&out=xls"

        # # https://www.scimagojr.com/journalrank.php?area=1200&out=xls
        # print(url_temp)
        # download_url(url_temp, path_csv_temp)
        path_csv_temp = "scimagojr 2024  Subject Area - Computer Science.csv"
        temp_df = pd.read_csv(path_csv_temp, sep=";")
        final_df = pd.DataFrame(columns=temp_df.columns)
        suffix = ""
        for area, subarea in filter_area.items():
            area_subare_df = dataframe_update(
                temp_df=temp_df, filter_area=area, filter_subareas=subarea)
            if mode == "aggregative":
                final_df = pd.concat([final_df,area_subare_df])
            else: 
                temp_df = area_subare_df
                
            suffix += f"{area}_" + "_".join(subarea)
        
         
        out_dir = f"outs/{suffix}/"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        if not mode == "aggregative":
            final_df = temp_df
        # print(temp_df)
        # print(temp_df.columns)

        ## final format
        if pivot_sub_area_code:
            final_df = final_df[["Rank", "SJR", "Title", "SJR Quartile", "H index", "Publisher", "Areas", "Categories"]]
        else:
            final_df = final_df[["Rank", "SJR", "Title", "SJR Best Quartile",
                        "H index", "Publisher", "Areas", "Categories"]]
        
        final_df["SJR"] = final_df["SJR"].apply(
            lambda x: float(str(x).replace(",", ".")))
        # temp_df.to_csv(f"{subfolder_path}{filter_area}_{contribution_name}.csv", index=False)
        final_df.to_csv(f"{out_dir}/{suffix}_{contr_type}.csv", index=False)
        final_df.to_excel(f"{out_dir}/{suffix}_{contr_type}.xlsx", index=False)