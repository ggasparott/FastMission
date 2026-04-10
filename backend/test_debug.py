import os, sys, json, subprocess
from dotenv import load_dotenv

load_dotenv(os.path.abspath('../.env'))

print('\n' + '='*80)
print('[QUICK DEBUG] Pipeline IA')
print('='*80)

# Teste 1: Subprocess
entrada = {
    'descricao': 'Camiseta',
    'ncm': '61045090',
    'cest': '16000',
    'regime_empresa': 'LUCRO_REAL',
    'uf_origem': 'SP',
    'uf_destino': 'RJ',
    'cnae_principal': '4719900'
}

script_path = 'skills/validate_reforma.py'

print('\n[TEST 1] Subprocess validate_reforma.py')
print('-'*80)
print('Script: ' + script_path)
print('Existe: ' + str(os.path.exists(script_path)))

entrada_json = json.dumps(entrada, ensure_ascii=False)
print('Processando...')

try:
    processo = subprocess.Popen(
        [sys.executable, script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd(),
        env=os.environ.copy()
    )
    stdout, stderr = processo.communicate(input=entrada_json, timeout=120)

    print('Return code: ' + str(processo.returncode))

    if stderr:
        print('\n[STDERR] (primeiros 2000 chars):')
        print(stderr[:2000])

    if stdout:
        print('\n[STDOUT] (primeiros 2000 chars):')
        print(stdout[:2000])

        # Extrair JSON
        for line in stdout.split('\n'):
            if line.strip().startswith('{'):
                try:
                    resultado = json.loads(line)
                    print('\n[JSON PARSEADO]')
                    print('  Status: ' + str(resultado.get('status')))
                    print('  Confianca: ' + str(resultado.get('confianca')))
                    print('  Regime: ' + str(resultado.get('regime_tributario')))
                    if resultado.get('status') == 'ERRO':
                        print('  ERRO: ' + str(resultado.get('explicacao'))[:300])
                    break
                except:
                    pass

except Exception as e:
    print('ERRO: ' + str(e))
    import traceback
    traceback.print_exc()

# Teste 2: chamar_ai_script direto
print('\n[TEST 2] chamar_ai_script()')
print('-'*80)

try:
    from app.tasks import chamar_ai_script
    print('Chamando...')
    resultado = chamar_ai_script('Camiseta 100% Algodao', '61045090', '16000', 'LUCRO_REAL', 'SP', 'RJ', '4719900')
    print('OK - Retornou')
    print('  Status: ' + str(resultado.get('status')))
    print('  Confianca: ' + str(resultado.get('confianca')))
    print('  Regime: ' + str(resultado.get('regime_tributario')))
    if resultado.get('status') == 'ERRO':
        print('  ERRO: ' + str(resultado.get('explicacao'))[:300])
except Exception as e:
    print('ERRO: ' + str(e))
    import traceback
    traceback.print_exc()

print('\n' + '='*80)
