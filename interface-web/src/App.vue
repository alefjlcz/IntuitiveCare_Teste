<script setup>
import { ref, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

// --- ESTADO ---
const operadoras = ref([])
const termoBusca = ref('')
const filtroUF = ref('')
const listaUFs = ref([])
const carregando = ref(false)
const erro = ref(null)
const page = ref(1)
const totalPaginas = ref(1)
const operadoraSelecionada = ref(null)
const historicoSelecionado = ref([]) // Armazena os dados do histórico

// Controles do Gráfico Principal
const mostrarGrafico = ref(false)
const dadosGrafico = ref({ labels: [], datasets: [] })
const graficoCarregado = ref(false)
const opcoesGrafico = { 
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, title: { display: true, text: 'Top 10 Estados (Geral)' } }
}

// --- FUNÇÕES ---

const carregarUFs = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/ufs')
    listaUFs.value = await res.json()
  } catch (e) {}
}

const carregarGrafico = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/estatisticas/uf')
    const json = await res.json()
    dadosGrafico.value = {
      labels: json.labels,
      datasets: [{ label: 'Total (R$)', backgroundColor: '#34495e', data: json.values, borderRadius: 4 }]
    }
    graficoCarregado.value = true
  } catch (e) {}
}

const buscarOperadoras = async () => {
  carregando.value = true
  try {
    const url = `http://127.0.0.1:8000/api/operadoras?search=${termoBusca.value}&uf=${filtroUF.value}&page=${page.value}`
    const response = await fetch(url)
    const dados = await response.json()
    if (dados.data) {
        operadoras.value = dados.data
        if (dados.meta) totalPaginas.value = dados.meta.pages
    }
  } catch (e) {
    erro.value = "Erro na conexão com a API."
  } finally {
    carregando.value = false
  }
}

// FUNÇÃO PARA ABRIR DETALHES E BUSCAR HISTÓRICO
const abrirDetalhes = async (op) => {
  operadoraSelecionada.value = op
  historicoSelecionado.value = []
  
  try {
    // Limpa o CNPJ para a URL da API
    const cnpjLimpo = (op.CNPJ || '').replace(/[./-]/g, '')
    const res = await fetch(`http://127.0.0.1:8000/api/operadoras/${cnpjLimpo}/despesas`)
    if (res.ok) {
      historicoSelecionado.value = await res.json()
    }
  } catch (e) {
    console.error("Erro ao buscar histórico:", e)
  }
}

const aplicarFiltro = () => { page.value = 1; buscarOperadoras() }
const mudarPagina = (p) => { if (p >= 1 && p <= totalPaginas.value) { page.value = p; buscarOperadoras() } }
const formatarMoeda = (v) => (v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

onMounted(() => {
  buscarOperadoras()
  carregarGrafico()
  carregarUFs()
})
</script>

<template>
  <div class="container">
    <header>
      <h1>IntuitiveCare - Dashboard ANS</h1>
      <p>Dados de 1.110 operadoras e histórico consolidado</p>
    </header>

    <div class="controles-grafico">
      <button @click="mostrarGrafico = !mostrarGrafico" class="btn-toggle">
        {{ mostrarGrafico ? 'Ocultar Gráfico' : 'Ver Estatísticas por Estado 📊' }}
      </button>
    </div>

    <div class="chart-container" v-if="mostrarGrafico && graficoCarregado">
      <Bar :data="dadosGrafico" :options="opcoesGrafico" />
    </div>

    <div class="filtros-container">
      <div class="campo-filtro">
        <label>Estado (UF):</label>
        <select v-model="filtroUF" @change="aplicarFiltro">
          <option value="">Brasil (Todos)</option>
          <option v-for="uf in listaUFs" :key="uf" :value="uf">{{ uf }}</option>
        </select>
      </div>
      <div class="campo-busca">
        <label>Pesquisar:</label>
        <input v-model="termoBusca" @keyup.enter="aplicarFiltro" placeholder="Nome, CNPJ ou Registro ANS..." type="text">
        <button @click="aplicarFiltro">🔍</button>
      </div>
    </div>

    <div v-if="!carregando && operadoras.length > 0">
      <table>
        <thead>
          <tr>
            <th>Reg. ANS</th>
            <th>Razão Social</th>
            <th>UF</th>
            <th class="valor">Despesas Totais</th>
            <th class="acao">Ação</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="op in operadoras" :key="op.id">
            <td>{{ op.Registro_ANS }}</td>
            <td>{{ op.Razao_Social }}</td>
            <td><span class="tag-uf">{{ op.UF }}</span></td>
            <td class="valor">{{ formatarMoeda(op.total_despesas || op.Total_Despesas) }}</td>
            <td class="acao"><button class="btn-detalhes" @click="abrirDetalhes(op)">Ver</button></td>
          </tr>
        </tbody>
      </table>
      
      <div class="pagination">
        <button :disabled="page <= 1" @click="mudarPagina(page - 1)">Anterior</button>
        <span>Página {{ page }} de {{ totalPaginas }}</span>
        <button :disabled="page >= totalPaginas" @click="mudarPagina(page + 1)">Próxima</button>
      </div>
    </div>

    <div v-if="operadoraSelecionada" class="modal-overlay" @click.self="operadoraSelecionada = null">
      <div class="modal">
        <div class="modal-header">
          <h2>Ficha da Operadora</h2>
        </div>
        <div class="modal-content">
          <p><strong>Razão Social:</strong> {{ operadoraSelecionada.Razao_Social }}</p>
          <p><strong>CNPJ:</strong> {{ operadoraSelecionada.CNPJ }}</p>
          <p><strong>Registro ANS:</strong> {{ operadoraSelecionada.Registro_ANS }}</p>
          
          <div class="secao-historico" v-if="historicoSelecionado.length > 0">
            <hr>
            <h3>Evolução das Despesas</h3>
            <div class="lista-historico">
              <div v-for="h in historicoSelecionado" :key="h.Data" class="item-historico">
                <span class="data-base">{{ h.Data }}</span>
                <span class="valor-base">{{ formatarMoeda(h.Valor) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="aviso-vazio">Buscando histórico detalhado...</div>
        </div>
        <button class="btn-fechar" @click="operadoraSelecionada = null">Fechar</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container { max-width: 1100px; margin: 0 auto; padding: 20px; font-family: sans-serif; }
header { text-align: center; margin-bottom: 30px; }
.filtros-container { display: flex; gap: 20px; background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; align-items: flex-end; }
.campo-busca { flex: 1; display: flex; flex-direction: column; gap: 5px; }
.campo-busca input { padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
.campo-busca button { background: #42b883; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer; }

table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th { background: #2c3e50; color: white; padding: 12px; text-align: left; }
td { padding: 12px; border-bottom: 1px solid #eee; }
.valor { text-align: right; font-weight: bold; }
.tag-uf { background: #e0e0e0; padding: 3px 6px; border-radius: 4px; font-size: 12px; }
.btn-detalhes { background: #3498db; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal { background: white; width: 500px; max-height: 80vh; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.modal-header { background: #2c3e50; color: white; padding: 15px; text-align: center; }
.modal-content { padding: 20px; overflow-y: auto; flex: 1; }
.item-historico { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f1f1f1; }
.data-base { font-weight: bold; color: #555; }
.valor-base { color: #27ae60; font-weight: bold; }
.btn-fechar { padding: 15px; background: #e74c3c; color: white; border: none; cursor: pointer; width: 100%; }
.pagination { display: flex; justify-content: center; gap: 20px; margin-top: 30px; }
</style>