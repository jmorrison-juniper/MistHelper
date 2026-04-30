import pandas as pd
from difflib import SequenceMatcher
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from datetime import datetime, timezone

# Load the CSV files
tmo_df = pd.read_csv("tmo_addresses.csv")
sites_df = pd.read_csv("SitesWithLocations.csv")

# Reconstruct full addresses from the TMO dataset
tmo_df['SAP ID'] = tmo_df['SAP ID'].astype(str).str.zfill(4)
tmo_df['full_address'] = (
    tmo_df['Address'].astype(str) + ', ' +
    tmo_df['City'].astype(str) + ', ' +
    tmo_df['State'].astype(str) + ' ' +
    tmo_df['Zip'].astype(str)
)

# Ensure Mist site addresses and names are strings
sites_df['address'] = sites_df['address'].astype(str)
sites_df['name'] = sites_df['name'].astype(str)

# Create a lookup dictionary for SAP ID suffix matching
sap_lookup = {
    site['name'][-4:]: (site['name'], site['address'])
    for _, site in sites_df.iterrows()
    if site['name'][-4:].isdigit()
}

# Function to compare a single TMO address
def compare_tmo_address(row):
    sap_id = str(row['SAP ID']).zfill(4)
    tmo_address = row['full_address']

    for _, site_row in sites_df.iterrows():
        site_name = site_row['name']
        site_address = site_row['address']
        similarity = SequenceMatcher(None, tmo_address.lower(), site_address.lower()).ratio()
        if similarity >= 0.9:
            return (sap_id, tmo_address, site_name, site_address, "fuzzy")

    if sap_id in sap_lookup:
        site_name, site_address = sap_lookup[sap_id]
        return (sap_id, tmo_address, site_name, site_address, "sap_id")

    return (sap_id, tmo_address, None, None, "unmatched")

# Function to compare a single Mist site address
def compare_site_address(row, tmo_addresses):
    site_name = row['name']
    site_address = row['address']

    for tmo_row in tmo_addresses:
        tmo_address = tmo_row['full_address']
        similarity = SequenceMatcher(None, site_address.lower(), tmo_address.lower()).ratio()
        if similarity >= 0.9:
            return (site_name, site_address, tmo_row['SAP ID'], tmo_address, "fuzzy")

    return (site_name, site_address, None, None, "unmatched")

# Wrapper to allow multiprocessing with extra arguments
def compare_site_address_wrapper(args):
    return compare_site_address(*args)

if __name__ == "__main__":
    print("🔍 Comparing addresses with fuzzy and SAP ID suffix matching...")

    # First pass: TMO to Mist
    with Pool(processes=cpu_count()) as pool:
        tmo_results = list(tqdm(pool.imap(compare_tmo_address, tmo_df.to_dict(orient="records")), total=len(tmo_df), desc="TMO Progress"))

    # Collect matched Mist site names from first pass
    matched_mist_sites = {r[2] for r in tmo_results if r[4] != "unmatched"}

    # Prepare unmatched Mist sites for second pass
    unmatched_sites_df = sites_df[~sites_df['name'].isin(matched_mist_sites)]

    # Prepare arguments for multiprocessing
    site_args = [(row, tmo_df.to_dict(orient="records")) for _, row in unmatched_sites_df.iterrows()]

    # Second pass: Mist to TMO using multiprocessing
    with Pool(processes=cpu_count()) as pool:
        site_results = list(tqdm(pool.imap(compare_site_address_wrapper, site_args), total=len(site_args), desc="Site Progress"))

    # Filter out None results
    site_results = [r for r in site_results if r is not None]

    # Count matches and unmatched
    tmo_matched = sum(1 for r in tmo_results if r[4] != "unmatched")
    tmo_unmatched = len(tmo_results) - tmo_matched
    site_matched = sum(1 for r in site_results if r[4] != "unmatched")
    site_unmatched = len(site_results) - site_matched

    # Write results to a log file
    with open("address_comparison_results.txt", "w", encoding="utf-8") as f:
        f.write(f"Comparison run at: {datetime.now(timezone.utc).isoformat()}\n\n")

        for sap_id, tmo_addr, site_name, site_addr, match_type in tmo_results:
            if match_type == "unmatched":
                f.write(f"❌ Unmatched TMO: SAP ID {sap_id}, Address: {tmo_addr}\n")
            else:
                f.write(f"✅ Matched TMO ({match_type}): SAP ID {sap_id}, TMO: {tmo_addr} <--> Mist: {site_name} \n {site_addr}\n")

        for site_name, site_addr, sap_id, tmo_addr, match_type in site_results:
            if match_type == "unmatched":
                f.write(f"❌ Unmatched Mist: Site Name {site_name}, Address: {site_addr}\n")

        # Summary
        f.write("\n📊 Summary:\n")
        f.write(f"TMO Matches: {tmo_matched}, Unmatched: {tmo_unmatched}\n")
        f.write(f"Mist Matches (excluding already matched): {site_matched}, Unmatched: {site_unmatched}\n")

    print("📄 Results written to 'address_comparison_results.txt'")
