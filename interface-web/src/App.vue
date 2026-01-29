<script setup>
import { ref, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const operadoras = ref([])
const termoBusca = ref('')
const filtroUF = ref('')
const listaUFs = ref([])
const carregando = ref(false)
const erro = ref(null)
const page = ref(1)
const totalPaginas = ref(1)
const operadoraSelecionada = ref(null)

// Visual do Gráfico
const mostrarGrafico = ref(false)
const dadosGrafico = ref({ labels: [], datasets: [] })
const graficoCarregado = ref(false)
const opcoesGrafico = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, title: { display: true, text: 'Top 10 Estados (Geral)' } }
}

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
    } else {
        operadoras.value = []
    }
  } catch (e) {
    erro.value = "Erro na conexão."
  } finally {
    carregando.value = false
  }
}

const aplicarFiltro = () => { page.value = 1; buscarOperadoras() }
const mudarPagina = (p) => { if (p >= 1 && p <= totalPaginas.value) { page.value = p; buscarOperadoras() } }
const formatarMoeda = (v) => (v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const abrirDetalhes = (op) => { operadoraSelecionada.value = op }

onMounted(() => {
  buscarOperadoras()
  carregarGrafico()
  carregarUFs()
})
</script>

<template>
  <div class="container">
    <header>
      <h1>IntuitiveCare - Busca de Operadoras</h1>
      <p>Dados consolidados da ANS (Financeiro + Cadastral)</p>
    </header>

    <div class="controles-grafico">
      <button @click="mostrarGrafico = !mostrarGrafico" class="btn-toggle">
        {{ mostrarGrafico ? 'Ocultar Gráfico' : 'Ver Estatísticas por Estado 📊' }}
      </button>
    </div>

    <div class="chart-container" v-if="mostrarGrafico && graficoCarregado">
      <Bar :data="dadosGrafico" :options="opcoesGrafico" />
    </div>

    <hr class="divisor">

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
        <input v-model="termoBusca" @keyup.enter="aplicarFiltro" placeholder="Nome ou CNPJ..." type="text">
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
            <th class="acao">Detalhes</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(op, index) in operadoras" :key="index">
            <td>{{ op.Registro_ANS || op.REG_ANS || '-' }}</td>
            <td>{{ op.Razao_Social }}</td>
            <td><span class="tag-uf">{{ op.UF }}</span></td>
            <td class="valor">{{ formatarMoeda(op.total_despesas || op.Total_Despesas) }}</td>
            <td class="acao"><button class="btn-detalhes" @click="abrirDetalhes(op)">Ver</button></td>
          </tr>
        </tbody>
      </table>

      <div class="pagination">
        <button :disabled="page <= 1" @click="mudarPagina(page - 1)">Anterior</button>
        <span>Pág. {{ page }} / {{ totalPaginas }}</span>
        <button :disabled="page >= totalPaginas" @click="mudarPagina(page + 1)">Próxima</button>
      </div>
    </div>

    <div v-if="!carregando && operadoras.length === 0" class="empty">
      Nenhum resultado encontrado.
    </div>

    <div v-if="operadoraSelecionada" class="modal-overlay" @click.self="operadoraSelecionada = null">
      <div class="modal">
        <div class="modal-header">
          <h2>Ficha da Operadora</h2>
        </div>
        <div class="modal-content">
          <div class="linha-detalhe">
            <strong>Razão Social:</strong>
            <span>{{ operadoraSelecionada.Razao_Social }}</span>
          </div>
          <div class="linha-detalhe">
            <strong>Registro ANS:</strong>
            <span class="destaque-azul">{{ operadoraSelecionada.Registro_ANS || '-' }}</span>
          </div>
          <div class="linha-detalhe">
            <strong>CNPJ:</strong>
            <span>{{ operadoraSelecionada.CNPJ || 'Não informado' }}</span>
          </div>
          <div class="linha-detalhe">
            <strong>UF:</strong>
            <span>{{ operadoraSelecionada.UF }}</span>
          </div>

          <hr>

          <div class="box-valor">
            <small>Total de Despesas Acumuladas</small>
            <h3>{{ formatarMoeda(operadoraSelecionada.total_despesas || operadoraSelecionada.Total_Despesas) }}</h3>
          </div>
        </div>
        <button class="btn-fechar" @click="operadoraSelecionada = null">Fechar</button>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* Estilos aprimorados */
.container { max-width: 1000px; margin: 0 auto; padding: 20px; font-family: 'Segoe UI', sans-serif; color: #333; }
header { text-align: center; margin-bottom: 20px; }
.divisor { margin: 20px 0; border: 0; border-top: 1px solid #ddd; }

.filtros-container { display: flex; gap: 15px; background: #f1f2f6; padding: 20px; border-radius: 8px; margin-bottom: 20px; align-items: flex-end; }
.campo-filtro, .campo-busca { display: flex; flex-direction: column; gap: 5px; }
.campo-busca { flex: 1; }
input, select { padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
.campo-busca input { width: 100%; }
.btn-toggle { background: #57606f; color: white; padding: 10px 20px; border: none; border-radius: 20px; cursor: pointer; display: block; margin: 0 auto 20px; }

table { width: 100%; border-collapse: collapse; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
th { background: #2f3542; color: white; padding: 12px; text-align: left; font-size: 0.9em; }
td { padding: 12px; border-bottom: 1px solid #eee; }
.tag-uf { background: #dfe4ea; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
.valor { text-align: right; font-family: monospace; font-weight: bold; }
.btn-detalhes { background: #1e90ff; color: white; border: none; padding: 5px 15px; border-radius: 4px; cursor: pointer; }

/* Modal Estilo Cartão */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 999; }
.modal { background: white; width: 450px; border-radius: 10px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.3); animation: fadeIn 0.3s; }
.modal-header { background: #2f3542; color: white; padding: 15px; text-align: center; }
.modal-content { padding: 20px; }
.linha-detalhe { display: flex; justify-content: space-between; margin-bottom: 12px; border-bottom: 1px solid #f1f1f1; padding-bottom: 5px; }
.destaque-azul { color: #1e90ff; font-weight: bold; }
.box-valor { background: #f1f2f6; padding: 15px; text-align: center; border-radius: 8px; margin-top: 15px; }
.box-valor h3 { margin: 5px 0 0; color: #27ae60; font-size: 1.5em; }
.btn-fechar { width: 100%; padding: 15px; background: #ff4757; color: white; border: none; cursor: pointer; font-size: 1em; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
.pagination { display: flex; justify-content: center; gap: 10px; margin-top: 20px; }
.empty { text-align: center; color: gray; margin: 20px; }
</style>