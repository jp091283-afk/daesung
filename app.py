import os, ssl, json, re
import requests
from flask import Flask, send_file, request, Response, jsonify

app = Flask(__name__)

# ── 환경변수로 관리 (Render 대시보드에서 설정) ──
DART_KEY  = os.environ.get('DART_KEY', '')
GROQ_KEY  = os.environ.get('GROQ_KEY', '')
LAW_KEY   = os.environ.get('LAW_KEY', '240713')

# ── index.html 서빙 (키 자동 주입) ──
@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # GROQ_KEY: 환경변수 있으면 더미 'proxied' 주입 (실제 키는 서버에만 존재)
    if GROQ_KEY and GROQ_KEY.strip():
        html = re.sub(
            r'GROQ_KEY="[^"]*"',
            'GROQ_KEY="proxied"',
            html, count=1
        )

    return Response(html, mimetype='text/html; charset=utf-8')

# ── DART API 프록시 ──
@app.route('/api/dart')
def dart_proxy():
    if not DART_KEY:
        return jsonify({'status': 'ERR', 'message': 'DART_KEY 환경변수가 설정되지 않았습니다.'}), 500

    qs = request.query_string.decode()
    qs = re.sub(r'crtfc_key=[^&]*', f'crtfc_key={DART_KEY}', qs)
    if 'crtfc_key' not in qs:
        qs = f'crtfc_key={DART_KEY}&' + qs

    dart_url = f'https://opendart.fss.or.kr/api/list.json?{qs}'

    try:
        resp = requests.get(
            dart_url,
            headers={'User-Agent': 'Mozilla/5.0 Chrome/120', 'Accept': 'application/json'},
            timeout=15,
            verify=False
        )
        body = resp.content
    except Exception as e:
        body = json.dumps({'status': 'ERR', 'message': str(e)}).encode()

    return Response(body, status=200,
                    mimetype='application/json; charset=utf-8',
                    headers={'Access-Control-Allow-Origin': '*'})

# ── DART 공시통합검색 프록시 ──
@app.route('/api/dart-search')
def dart_search():
    keyword = request.args.get('keyword', '')
    page    = request.args.get('currentPage', '1')
    max_r   = request.args.get('maxResults', '15')

    from urllib.parse import quote
    search_url = (
        'https://dart.fss.or.kr/dsab007/searchAjax.do'
        f'?keyword={quote(keyword)}'
        f'&currentPage={page}'
        f'&maxResults={max_r}'
        '&sort=date&desc=true'
    )
    try:
        resp = requests.get(
            search_url,
            headers={
                'User-Agent': 'Mozilla/5.0 Chrome/120',
                'Accept': 'application/json, text/html, */*',
                'Referer': 'https://dart.fss.or.kr/',
            },
            timeout=15,
            verify=False
        )
        body = resp.content
        ct   = resp.headers.get('Content-Type', 'application/json')
    except Exception as e:
        bo
