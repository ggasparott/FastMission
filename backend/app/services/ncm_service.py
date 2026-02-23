"""
Service Layer - NCM (Nomenclatura Comum do Mercosul)

Responsabilidades:
- Validação de códigos NCM
- Autocomplete e busca por prefixo
- Fuzzy matching para correção de NCMs inválidos
- Sincronização com API ComexStat (futuro)
- Cache local de NCMs oficiais
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models import NCMOficial
from app.repositories.ncm_repository import NCMRepository


class NCMNotFoundException(Exception):
    """Exceção lançada quando um NCM não é encontrado"""
    pass


class NCMValidationError(Exception):
    """Exceção lançada quando há erro de validação de NCM"""
    pass


class NCMService:
    """
    Service para operações de negócio relacionadas a NCM.
    
    Fornece validação, autocomplete, fuzzy matching e sugestão
    de NCMs válidos baseados em descrição e similaridade.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o service com as dependências necessárias.
        
        Args:
            db: Sessão do SQLAlchemy
        """
        self.db = db
        self.ncm_repo = NCMRepository(db)
    
    
    def validar_ncm(self, codigo: str) -> Dict[str, Any]:
        """
        Valida se um código NCM existe e está correto.
        
        Args:
            codigo: Código NCM (8 dígitos)
        
        Returns:
            Dicionário com resultado da validação:
                - valido: True/False
                - ncm: objeto NCMOficial (se encontrado)
                - mensagem: mensagem descritiva
                - sugestoes: lista de NCMs similares (se inválido)
        
        Exemplo:
            resultado = service.validar_ncm("10063021")
            
            if resultado['valido']:
                print(f"NCM válido: {resultado['ncm'].descricao}")
            else:
                print(f"NCM inválido: {resultado['mensagem']}")
                print(f"Sugestões: {resultado['sugestoes']}")
        """
        # Normalizar código (remover pontos, espaços, etc)
        codigo_limpo = self._normalizar_codigo_ncm(codigo)
        
        # Validar formato básico (8 dígitos)
        if not self._validar_formato_ncm(codigo_limpo):
            return {
                "valido": False,
                "ncm": None,
                "mensagem": f"Formato inválido. NCM deve ter 8 dígitos. Recebido: {codigo}",
                "sugestoes": []
            }
        
        # Buscar NCM no banco
        ncm = self.ncm_repo.buscar_por_codigo(codigo_limpo)
        
        if ncm:
            return {
                "valido": True,
                "ncm": ncm,
                "mensagem": "NCM válido",
                "sugestoes": []
            }
        else:
            # NCM não encontrado - buscar similares
            sugestoes = self.buscar_similares(codigo_limpo, limit=5)
            
            return {
                "valido": False,
                "ncm": None,
                "mensagem": f"NCM {codigo_limpo} não encontrado na base de dados",
                "sugestoes": sugestoes
            }
    
    
    def autocomplete(self, prefixo: str, limit: int = 10) -> List[NCMOficial]:
        """
        Retorna NCMs que começam com o prefixo informado.
        
        Útil para autocomplete em interfaces de usuário.
        
        Args:
            prefixo: Início do código NCM (ex: "1006")
            limit: Quantidade máxima de resultados
        
        Returns:
            Lista de NCMs que começam com o prefixo
        
        Exemplo:
            # Usuário digitou "1006"
            sugestoes = service.autocomplete("1006", limit=10)
            
            for ncm in sugestoes:
                print(f"{ncm.codigo} - {ncm.descricao}")
            
            # Output:
            # 10061010 - Arroz com casca (arroz "paddy"), parboilizado
            # 10061090 - Outros arrozes com casca
            # 10062010 - Arroz descascado (arroz "cargo" ou castanho), parboilizado
            # ...
        """
        # Normalizar prefixo
        prefixo_limpo = self._normalizar_codigo_ncm(prefixo)
        
        # Validar que não está vazio
        if not prefixo_limpo:
            return []
        
        # Buscar por prefixo
        return self.ncm_repo.buscar_por_prefixo(prefixo_limpo, limit=limit)
    
    
    def buscar_por_descricao(self, termo: str, limit: int = 10) -> List[NCMOficial]:
        """
        Busca NCMs por termo na descrição.
        
        Args:
            termo: Palavra ou frase a buscar (ex: "arroz", "café")
            limit: Quantidade máxima de resultados
        
        Returns:
            Lista de NCMs cuja descrição contém o termo
        
        Exemplo:
            # Buscar todos os NCMs de café
            cafes = service.buscar_por_descricao("café", limit=20)
            
            for ncm in cafes:
                print(f"{ncm.codigo} - {ncm.descricao}")
        """
        if not termo or len(termo.strip()) < 2:
            raise NCMValidationError("Termo de busca deve ter pelo menos 2 caracteres")
        
        return self.ncm_repo.buscar_por_descricao(termo, limit=limit)
    
    
    def buscar_similares(
        self, 
        codigo: str, 
        limit: int = 5,
        max_distancia: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Busca NCMs similares usando algoritmo de distância de Levenshtein.
        
        Útil para sugerir correções quando um NCM está incorreto.
        
        Args:
            codigo: Código NCM a comparar
            limit: Quantidade máxima de sugestões
            max_distancia: Distância máxima de Levenshtein para considerar similar
        
        Returns:
            Lista de dicionários com NCM e score de similaridade
        
        Exemplo:
            # NCM digitado errado: "10063022" (correto: "10063021")
            similares = service.buscar_similares("10063022", limit=5)
            
            for sugestao in similares:
                print(f"{sugestao['codigo']} - Distância: {sugestao['distancia']}")
                print(f"  {sugestao['descricao']}")
            
            # Output:
            # 10063021 - Distância: 1
            #   Arroz semibranqueado ou branqueado
        """
        # Normalizar código
        codigo_limpo = self._normalizar_codigo_ncm(codigo)
        
        # Buscar NCMs por prefixo (primeiros 4 dígitos) para limitar busca
        prefixo = codigo_limpo[:4]
        candidatos = self.ncm_repo.buscar_por_prefixo(prefixo, limit=100)
        
        # Se não encontrou nada com o prefixo, buscar mais amplo
        if not candidatos:
            candidatos = self.ncm_repo.buscar_por_prefixo(codigo_limpo[:2], limit=100)
        
        # Calcular distância de Levenshtein para cada candidato
        resultados = []
        for ncm in candidatos:
            distancia = self._calcular_distancia_levenshtein(codigo_limpo, ncm.codigo)
            
            if distancia <= max_distancia:
                resultados.append({
                    "codigo": ncm.codigo,
                    "descricao": ncm.descricao,
                    "distancia": distancia,
                    "similaridade_percentual": (1 - distancia / max(len(codigo_limpo), len(ncm.codigo))) * 100
                })
        
        # Ordenar por distância (menor distância = mais similar)
        resultados.sort(key=lambda x: x['distancia'])
        
        return resultados[:limit]
    
    
    def sugerir_ncm_por_descricao(
        self, 
        descricao_produto: str, 
        limit: int = 5
    ) -> List[NCMOficial]:
        """
        Sugere NCMs baseado na descrição do produto.
        
        Esta é uma busca simples por palavras-chave.
        Para sugestões mais inteligentes, use o CrewAI GPTClassifierTool.
        
        Args:
            descricao_produto: Descrição do produto (ex: "ARROZ INTEGRAL 1KG")
            limit: Quantidade máxima de sugestões
        
        Returns:
            Lista de NCMs relacionados
        
        Exemplo:
            # Produto: "CAFÉ TORRADO EM GRÃOS 250G"
            sugestoes = service.sugerir_ncm_por_descricao("CAFÉ TORRADO EM GRÃOS", limit=5)
            
            for ncm in sugestoes:
                print(f"{ncm.codigo} - {ncm.descricao}")
        """
        # Extrair palavras-chave da descrição
        palavras_chave = self._extrair_palavras_chave(descricao_produto)
        
        if not palavras_chave:
            return []
        
        # Buscar pela primeira palavra-chave mais relevante
        # TODO: Melhorar algoritmo para combinar múltiplas palavras
        principal = palavras_chave[0]
        
        return self.buscar_por_descricao(principal, limit=limit)
    
    
    def sincronizar_com_comexstat(self, ncms_dados: List[Dict[str, Any]]) -> int:
        """
        Sincroniza base local de NCMs com dados do ComexStat.
        
        Este método será chamado por um Celery task periodicamente
        para manter a base atualizada.
        
        Args:
            ncms_dados: Lista de dicionários com dados de NCM do ComexStat
                Formato: [{"codigo": "10063021", "descricao": "Arroz..."}, ...]
        
        Returns:
            Quantidade de NCMs inseridos
        
        Exemplo:
            # Em uma Celery task
            ncms = buscar_ncms_comexstat()  # API externa
            total = service.sincronizar_com_comexstat(ncms)
            print(f"{total} NCMs sincronizados")
        """
        if not ncms_dados:
            return 0
        
        # Limpar tabela antes de inserir (dados do ComexStat são autoritativos)
        self.ncm_repo.limpar_tabela()
        
        # Inserir em lote
        total = self.ncm_repo.criar_lote(ncms_dados)
        
        return total
    
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da base de NCMs.
        
        Returns:
            Dicionário com estatísticas
        
        Exemplo:
            stats = service.obter_estatisticas()
            print(f"Total de NCMs: {stats['total_ncms']}")
            print(f"Última atualização: {stats['ultima_atualizacao']}")
        """
        total = self.ncm_repo.contar()
        
        return {
            "total_ncms": total,
            "base_populada": total > 0,
            # TODO: Adicionar data da última sincronização
        }
    
    
    # ========== MÉTODOS PRIVADOS (HELPERS) ==========
    
    def _normalizar_codigo_ncm(self, codigo: str) -> str:
        """
        Normaliza um código NCM removendo caracteres inválidos.
        
        Args:
            codigo: Código NCM bruto
        
        Returns:
            Código limpo (apenas dígitos)
        
        Exemplo:
            _normalizar_codigo_ncm("1006.30.21") -> "10063021"
            _normalizar_codigo_ncm("1006 3021") -> "10063021"
        """
        if not codigo:
            return ""
        
        # Remover tudo exceto dígitos
        return ''.join(c for c in str(codigo) if c.isdigit())
    
    
    def _validar_formato_ncm(self, codigo: str) -> bool:
        """
        Valida se o código NCM tem o formato correto (8 dígitos).
        
        Args:
            codigo: Código NCM (já normalizado)
        
        Returns:
            True se válido, False caso contrário
        """
        return len(codigo) == 8 and codigo.isdigit()
    
    
    def _calcular_distancia_levenshtein(self, s1: str, s2: str) -> int:
        """
        Calcula a distância de Levenshtein entre duas strings.
        
        Algoritmo de programação dinâmica O(n*m).
        
        Args:
            s1: Primeira string
            s2: Segunda string
        
        Returns:
            Distância de Levenshtein (quantidade mínima de edições)
        
        Exemplo:
            _calcular_distancia_levenshtein("10063021", "10063022") -> 1
            _calcular_distancia_levenshtein("kitten", "sitting") -> 3
        """
        if len(s1) < len(s2):
            return self._calcular_distancia_levenshtein(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        # Array anterior (linha i-1)
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            # Array atual (linha i)
            current_row = [i + 1]
            
            for j, c2 in enumerate(s2):
                # Custo de inserção, deleção ou substituição
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
               
                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    
    def _extrair_palavras_chave(self, descricao: str) -> List[str]:
        """
        Extrai palavras-chave de uma descrição de produto.
        
        Remove stopwords e retorna palavras mais relevantes.
        
        Args:
            descricao: Descrição do produto
        
        Returns:
            Lista de palavras-chave ordenadas por relevância
        
        Exemplo:
            _extrair_palavras_chave("ARROZ INTEGRAL TIPO 1 PACOTE 1KG")
            -> ["ARROZ", "INTEGRAL"]
        """
        # Stopwords em português (palavras irrelevantes)
        stopwords = {
            "DE", "DO", "DA", "DOS", "DAS", "EM", "NO", "NA", "NOS", "NAS",
            "O", "A", "OS", "AS", "UM", "UMA", "E", "OU", "PARA", "COM",
            "SEM", "POR", "TIPO", "PACOTE", "UNIDADE", "KG", "G", "ML", "L"
        }
        
        # Converter para maiúsculas e dividir em palavras
        palavras = descricao.upper().split()
        
        # Filtrar stopwords e palavras muito curtas
        palavras_chave = [
            p for p in palavras 
            if len(p) >= 3 and p not in stopwords
        ]
        
        return palavras_chave
