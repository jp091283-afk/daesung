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

    # GROQ_KEY: 환경변수 있으면 더미 'proxied' 주입
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
        body = json.dumps({'error': str(e), 'results': []}).encode()
        ct   = 'application/json'

    return Response(body, status=200, mimetype=ct,
                    headers={'Access-Control-Allow-Origin': '*'})

# ── Groq AI 프록시 ──
@app.route('/api/groq', methods=['POST'])
def groq_proxy():
    if not GROQ_KEY:
        return jsonify({'error': {'message': 'GROQ_KEY 환경변수가 설정되지 않았습니다.'}}), 500
    try:
        payload = request.get_json()
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {GROQ_KEY}'
            },
            json=payload,
            timeout=60
        )
        return Response(resp.content, status=resp.status_code,
                        mimetype='application/json; charset=utf-8',
                        headers={'Access-Control-Allow-Origin': '*'})
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 500

# ── 법령정보 프록시 ──
@app.route('/api/law')
def law_proxy():
    query = request.args.get('query', '')
    msr   = request.args.get('MSR', '')

    params = {'OC': LAW_KEY, 'target': 'law', 'type': 'JSON'}
    if query: params['query'] = query
    if msr:   params['MST']   = msr

    try:
        resp = requests.get(
            'http://www.law.go.kr/DRF/lawSearch.do',
            params=params,
            headers={'User-Agent': 'Mozilla/5.0 Chrome/120'},
            timeout=15
        )
        return Response(resp.content, status=200,
                        mimetype='application/json; charset=utf-8',
                        headers={'Access-Control-Allow-Origin': '*'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
