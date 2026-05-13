#!/usr/bin/env python3
"""
Fallback extractor for readtheone.com ranking pages.

Usage:
    python extract_readtheone_requests.py "<URL>" [--pages N]

Outputs a JSON array compatible with extract_readtheone.js:
    [{"rank":"1","company_name":"...","score":"...","reason":"...",
      "source":"...","track":"...","tags":["tag1","tag2"]}, ...]

Use this when agent-browser is unavailable (e.g. connection timeout on Windows).
"""

import argparse
import json
import re
import sys

import requests


def clean_emoji(text: str) -> str:
    if not text:
        return ''
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
    text = re.sub(r'[☀-⛿]', '', text)
    text = re.sub(r'[✀-➿]', '', text)
    text = re.sub(r'[🔗⚡🔥]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def strip_tags(html_fragment: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', html_fragment)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_page(url: str) -> list[dict]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    html = resp.text

    rows = re.findall(r'<div class="ranking-row[^"]*"[^>]*>(.*?)\n\s*</div>', html, re.DOTALL)

    data = []
    for block in rows:
        rank_match = re.search(r'<span class="col-rank[^"]*"[^>]*>(.*?)</span>', block, re.DOTALL)
        rank = clean_emoji(strip_tags(rank_match.group(1) if rank_match else ''))

        name_match = re.search(r'<span class="col-name[^"]*"[^>]*>(.*?)</span>', block, re.DOTALL)
        if not name_match:
            name_match = re.search(r'<div class="col-name[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
        name_block = name_match.group(1) if name_match else ''

        name_text_match = re.search(r'<span class="project-name-text[^"]*"[^>]*>(.*?)</span>', name_block, re.DOTALL)
        if name_text_match:
            name = clean_emoji(strip_tags(name_text_match.group(1)))
        else:
            name = clean_emoji(strip_tags(name_block))

        tags = []
        tag_container = re.search(r'<span class="project-inline-tags[^"]*"[^>]*>(.*?)</span>', name_block, re.DOTALL)
        if tag_container:
            tag_spans = re.findall(r'<span[^>]*>(.*?)</span>', tag_container.group(1), re.DOTALL)
            for t in tag_spans:
                t_clean = clean_emoji(strip_tags(t))
                if t_clean and t_clean != name:
                    tags.append(t_clean)

        score_match = re.search(r'<span class="col-score[^"]*"[^>]*>(.*?)</span>', block, re.DOTALL)
        if not score_match:
            score_match = re.search(r'<div class="col-score[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
        score = clean_emoji(strip_tags(score_match.group(1) if score_match else ''))

        reason_match = re.search(r'<span class="col-reason[^"]*"[^>]*>(.*?)</span>', block, re.DOTALL)
        if not reason_match:
            reason_match = re.search(r'<div class="col-reason[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
        reason = clean_emoji(strip_tags(reason_match.group(1) if reason_match else ''))

        source_match = re.search(r'<span class="col-source[^"]*"[^>]*>(.*?)</span>', block, re.DOTALL)
        if not source_match:
            source_match = re.search(r'<div class="col-source[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
        source_block = source_match.group(1) if source_match else ''
        source_val = clean_emoji(strip_tags(source_block))

        track_match = re.search(r'<span class="col-track[^"]*"[^>]*>(.*?)</span>', block, re.DOTALL)
        if not track_match:
            track_match = re.search(r'<div class="col-track[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
        track = clean_emoji(strip_tags(track_match.group(1) if track_match else ''))

        if name and name != '项目名称':
            data.append({
                'rank': rank,
                'company_name': name,
                'score': score,
                'reason': reason,
                'source': source_val,
                'track': track,
                'tags': tags,
            })
    return data


def main():
    parser = argparse.ArgumentParser(description='Extract readtheone ranking rows via requests (fallback for agent-browser)')
    parser.add_argument('url', help='Target URL (must contain page=1 if paginated)')
    parser.add_argument('--pages', type=int, default=1, help='Max pages to fetch (default: 1)')
    args = parser.parse_args()

    all_data = []
    for page in range(1, args.pages + 1):
        url = args.url.replace('page=1', f'page={page}')
        try:
            data = extract_page(url)
        except requests.RequestException as e:
            print(f'Error fetching page {page}: {e}', file=sys.stderr)
            break
        if not data:
            break
        all_data.extend(data)
        print(f'Page {page}: {len(data)} rows', file=sys.stderr)

    json.dump(all_data, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == '__main__':
    main()
