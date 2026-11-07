"""Bounded, unauthenticated diagnostics; never read .env or print error bodies."""
import concurrent.futures
import json
import os
import platform
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit


def check(kind, host):
    if kind == 'dns':
        try:
            addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            return {'status': 'ok', 'address_count': len({a[4][0] for a in addresses})}
        except OSError as error:
            return {'status': 'failed', 'exception': type(error).__name__, 'errno': error.errno}
    # Default proxy behavior and TLS verification remain enabled. No redirects.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    try:
        opener = urllib.request.build_opener(NoRedirect)
        with opener.open(urllib.request.Request('https://' + host + '/', method='HEAD'), timeout=8) as response:
            return {'status': 'http_response', 'http_status': response.status, 'tls_verified': True}
    except urllib.error.HTTPError as error:
        return {'status': 'http_response', 'http_status': error.code, 'tls_verified': True}
    except Exception as error:
        reason = getattr(error, 'reason', error)
        result = {'status': 'failed', 'exception': type(reason).__name__}
        if isinstance(reason, OSError):
            result['errno'] = reason.errno
        if isinstance(reason, ssl.SSLCertVerificationError):
            result['certificate_verify_code'] = reason.verify_code
        return result


def bounded(job):
    kind, host = job
    try:
        result = subprocess.run([sys.executable, __file__, '--worker', kind, host],
                                capture_output=True, text=True, timeout=10)
        value = json.loads(result.stdout) if result.returncode == 0 else {'status': 'worker_failed'}
    except subprocess.TimeoutExpired:
        value = {'status': 'timeout', 'limit_seconds': 10}
    return kind + ':' + host, value


def main():
    result = {'kernel': platform.release(), 'proxy_environment': {}, 'socket_creation': {}}
    for name in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy',
                 'all_proxy', 'NO_PROXY', 'no_proxy'):
        value = os.environ.get(name)
        entry = {'present': bool(value)}
        if value and name.lower() != 'no_proxy':
            try:
                parsed = urlsplit(value)
                entry.update(scheme=parsed.scheme, host=parsed.hostname, port=parsed.port,
                             credentials_present=bool(parsed.username or parsed.password))
            except ValueError:
                entry['parse_error'] = True
        result['proxy_environment'][name] = entry
    for label, kind in (('tcp', socket.SOCK_STREAM), ('udp', socket.SOCK_DGRAM)):
        try:
            with socket.socket(socket.AF_INET, kind):
                result['socket_creation'][label] = {'status': 'ok'}
        except OSError as error:
            result['socket_creation'][label] = {'status': 'failed', 'errno': error.errno}
    try:
        result['default_tls_trust'] = {'ca_count': len(ssl.create_default_context().get_ca_certs())}
    except Exception as error:
        result['default_tls_trust'] = {'exception': type(error).__name__}
    jobs = [(kind, host) for kind in ('dns', 'https') for host in
            ('generativelanguage.googleapis.com', 'api.openai.com', 'example.com')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        result['checks'] = dict(pool.map(bounded, jobs))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        print(json.dumps(check(sys.argv[2], sys.argv[3])))
    else:
        main()
