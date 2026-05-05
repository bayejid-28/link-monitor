import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import pandas as pd

def get_all_links(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a_tag in soup.find_all('a', href=True):
            full_url = urljoin(url, a_tag['href'])
            if urlparse(full_url).scheme in ['http', 'https']:
                links.append({"source": url, "link": full_url})
        return links
    except:
        return []

def check_link(item):
    skip_domains = ['facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com']
    if any(domain in item["link"] for domain in skip_domains):
        return {
            "source_page": item["source"],
            "broken_url": item["link"],
            "status": "Skipped",
            "broken": False
        }
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(item["link"], timeout=10, headers=headers)
        return {
            "source_page": item["source"],
            "broken_url": item["link"],
            "status": response.status_code,
            "broken": response.status_code >= 400
        }
    except:
        return {
            "source_page": item["source"],
            "broken_url": item["link"],
            "status": "Timeout/Error",
            "broken": True
        }

# UI
st.title("🔗 Link Monitor")
st.subheader("Find all broken links on your website instantly")

website_url = st.text_input("Enter your website URL", placeholder="https://example.com")

if st.button("Start Scan"):
    if website_url:
        with st.spinner("Collecting links..."):
            links = get_all_links(website_url)
            st.info(f"Found {len(links)} links")

        with st.spinner("Checking links..."):
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(check_link, links))

        broken = [r for r in results if r['broken']]
        working = [r for r in results if not r['broken']]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Links", len(results))
        col2.metric("✅ Working", len(working))
        col3.metric("❌ Broken", len(broken))

        if broken:
            st.error(f"{len(broken)} broken links found!")

            df = pd.DataFrame([{
                "Source Page": r['source_page'],
                "Broken URL": r['broken_url'],
                "Status": r['status']
            } for r in broken])

            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="broken_links.csv",
                mime="text/csv"
            )
        else:
            st.success("Great! No broken links found. ✅")
    else:
        st.warning("Please enter a URL first!")