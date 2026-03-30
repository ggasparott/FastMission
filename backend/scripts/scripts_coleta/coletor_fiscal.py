import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

class BigDataTributario2026:
    def __init__(self):
        self.hoje = datetime.now().strftime('%Y-%m-%d')
        self.diretorio = f"database_tributaria_{self.hoje}"
        if not os.path.exists(self.diretorio):
            os.makedirs(self.diretorio)
        
        self.headers = {
            'User-Agent': 'Agente-Saneamento-IA-Varejo/2.0 (contato.fastdev@gmail.com)'
        }

    def _salvar_dados(self, nome, dados, formato='csv'):
        caminho = os.path.join(self.diretorio, f"{nome}.{formato}")
        if formato == 'csv':
            dados.to_csv(caminho, index=False, encoding='utf-8-sig')
        elif formato == 'json':
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
        print(f"✅ {nome} salvo com sucesso.")

    def fetch_ncm_completo(self):
        """Busca a árvore completa de NCM e Unidades de Medida."""
        print("🔍 Coletando NCM (Siscomex)...")
        url = "https://portalunico.siscomex.gov.br/classif/api/gcm/tabela/ncm"
        try:
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                self._salvar_dados("tabela_ncm_hierarquica", r.json(), 'json')
        except Exception as e: print(f"❌ Erro NCM: {e}")

    def fetch_cest_st(self):
        """Busca a tabela CEST e correlações com NCM (CONFAZ)."""
        print("🔍 Coletando CEST e Regras de ST...")
        url = "https://www.confaz.fazenda.gov.br/legislacao/convenios/2015/CV092_15"
        try:
            dfs = pd.read_html(url)
            df_final = pd.concat(dfs, ignore_index=True)
            self._salvar_dados("tabela_cest_consolidada", df_final)
        except Exception as e: print(f"❌ Erro CEST: {e}")

    def fetch_cnae_varejo(self):
        """Busca a lista de CNAEs para validação de perfil de cliente."""
        print("🔍 Coletando CNAEs (IBGE/CONCLA)...")
        url = "https://servicodados.ibge.gov.br/api/v2/cnae/subclasses"
        try:
            r = requests.get(url)
            df_cnae = pd.DataFrame(r.json())
            self._salvar_dados("lista_cnae_subclasses", df_cnae)
        except Exception as e: print(f"❌ Erro CNAE: {e}")

    def fetch_reforma_transicao_2026(self):
        """Busca e lista todos os links da página da Reforma Tributária para análise."""
        print("🔍 Coletando Regras da Reforma (IBS/CBS/Cashback)...")
        url = "https://www.gov.br/fazenda/pt-br/assuntos/reforma-tributaria"
        try:
            r = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(r.text, 'html.parser')
            todos_links = {}
            for link in soup.find_all('a', href=True):
                texto = link.text.strip()
                href = link['href']
                if texto:
                    todos_links[texto] = href
            print(f"🔗 {len(todos_links)} links encontrados na página. Salvando todos para análise...")
            self._salvar_dados("todos_links_reforma_2026", todos_links, 'json')
            # (Opcional) Exibir os primeiros links para debug rápido
            for i, (texto, href) in enumerate(todos_links.items()):
                if i < 10:
                    print(f"{texto}: {href}")
            print("⚠️  Revise o arquivo todos_links_reforma_2026.json para ajustar o filtro de regras.")
        except Exception as e:
            print(f"❌ Erro Reforma: {e}")

    def fetch_ibpt_taxas(self):
        print("🔍 Coletando Índices de Carga Tributária (IBPT/De Olho no Imposto)...")
        print("⚠️  Aviso: Para dados IBPT reais, integre sua API Key.")

    def executar_tudo(self):
        print(f"🚀 Iniciando Big Data Fiscal 2026...")
        self.fetch_ncm_completo()
        self.fetch_cest_st()
        self.fetch_cnae_varejo()
        self.fetch_reforma_transicao_2026()
        print(f"\n✨ Processo concluído! Dados prontos em: {self.diretorio}")

if __name__ == "__main__":
    extrator = BigDataTributario2026()
    extrator.executar_tudo()
