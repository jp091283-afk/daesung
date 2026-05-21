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

    # GROQ_KEY: 환경변수 있으면 교체, 없으면 HTML 하드코딩 키 그대로 사용
    if GROQ_KEY and GROQ_KEY.strip():
        html = re.sub(
            r'GROQ_KEY="[^"]*"',
            f'GROQ_KEY="{GROQ_KEY.strip()}"',
            html, count=1
        )
    if LAW_KEY:
        html = re.sub(
            r"(LAW_KEY\s*=\s*)['\"][^'\"]*['\"]",
            f'LAW_KEY = "{LAW_KEY}"',
            html, count=1
        )
    # DART_KEY는 서버에서 처리하므로 클라이언트에 빈값 유지
    # (브라우저 → /api/dart → 서버가 실제 키로 DART 호출)

    return Response(html, mimetype='text/html; charset=utf-8')

# ── DART API 프록시 ──
@app.route('/api/dart')
def dart_proxy():
    if not DART_KEY:
        return jsonify({'status': 'ERR', 'message': 'DART_KEY 환경변수가 설정되지 않았습니다.'}), 500

    # 쿼리스트링에서 crtfc_key 제거 후 서버 키 삽입
    from urllib.parse import urlencode, parse_qs, urlparse
    qs = request.query_string.decode()
    # crtfc_key 파라미터 교체
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

    return Response(
        body,
        status=200,
        mimetype='application/json; charset=utf-8',
        headers={'Access-Control-Allow-Origin': '*'}
    )

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
        body = json.dumps({'error': str(e), 'results': []}).encode()
        ct   = 'application/json'

    return Response(body, status=200, mimetype=ct,
                    headers={'Access-Control-Allow-Origin': '*'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
