import argparse
import requests
import json
import csv

ARXIV_API = "http://export.arxiv.org/api/query"
CROSSREF_API = "https://api.crossref.org/works"

def fetch_arxiv_dois(query, max_results=100):
    import xml.etree.ElementTree as ET
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    response = requests.get(ARXIV_API, params=params)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
    dois = []
    for entry in root.findall('.//atom:entry', ns):
        doi_elem = entry.find('.//arxiv:doi', ns)
        if doi_elem is not None:
            dois.append(doi_elem.text.strip())
    return dois

def fetch_crossref_dois(query, max_results=100):
    params = {
        'query': query,
        'rows': max_results
    }
    response = requests.get(CROSSREF_API, params=params)
    response.raise_for_status()
    data = response.json()
    dois = [item['DOI'] for item in data.get('message', {}).get('items', []) if 'DOI' in item]
    return dois

def save_json(dois, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(dois, f, indent=2, ensure_ascii=False)

def save_csv(dois, path):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['DOI'])
        for doi in dois:
            writer.writerow([doi])

def main():
    parser = argparse.ArgumentParser(description="Generate a list of DOIs from arXiv or CrossRef by keyword.")
    parser.add_argument('--arxiv', action='store_true', help='Query arXiv')
    parser.add_argument('--crossref', action='store_true', help='Query CrossRef')
    parser.add_argument('--query', required=True, help='Search query (keyword, author, etc.)')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum results to fetch')
    parser.add_argument('--output-json', help='Path to output JSON file')
    parser.add_argument('--output-csv', help='Path to output CSV file')
    args = parser.parse_args()

    dois = []
    if args.arxiv:
        print(f"[INFO] Querying arXiv for: {args.query}")
        dois.extend(fetch_arxiv_dois(args.query, args.max_results))
    if args.crossref:
        print(f"[INFO] Querying CrossRef for: {args.query}")
        dois.extend(fetch_crossref_dois(args.query, args.max_results))
    dois = list(sorted(set(dois)))
    print(f"[INFO] Found {len(dois)} unique DOIs.")
    if args.output_json:
        save_json(dois, args.output_json)
        print(f"[INFO] Saved DOIs to {args.output_json}")
    if args.output_csv:
        save_csv(dois, args.output_csv)
        print(f"[INFO] Saved DOIs to {args.output_csv}")
    if not args.output_json and not args.output_csv:
        print(json.dumps(dois, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 