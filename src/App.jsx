import { useState, useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { MapPin, Users, ChevronDown, ChevronUp } from 'lucide-react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'
import faminasLogo from './assets/logo_Faminas.png'

// Configurar ícones do Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

// Ajusta o enquadramento do mapa aos pontos filtrados
function FitBounds({ points }) {
  const map = useMap()
  useEffect(() => {
    if (points.length > 0) {
      map.fitBounds(points, { padding: [40, 40], maxZoom: 13 })
    }
  }, [points, map])
  return null
}

function App() {
  const [locations, setLocations] = useState([])
  const [filters, setFilters] = useState({})
  const [selectedFilters, setSelectedFilters] = useState({
    disciplina: '',
    atividade: '',
    especialidade: '',
    periodo: '',
    preceptor: '',
    cidade: ''
  })
  const [loading, setLoading] = useState(true)
  const [expandedCards, setExpandedCards] = useState(new Set())

  // Carregar dados
  useEffect(() => {
    const loadData = async () => {
      try {
        const [locationsResponse, filtersResponse] = await Promise.all([
          fetch('/locations.json'),
          fetch('/filters.json')
        ])

        const locationsData = await locationsResponse.json()
        const filtersData = await filtersResponse.json()

        setLocations(locationsData)
        setFilters(filtersData)
        setLoading(false)
      } catch (error) {
        console.error('Erro ao carregar dados:', error)
        setLoading(false)
      }
    }

    loadData()
  }, [])

  // Função para agrupar localizações por coordenadas
  const groupLocationsByCoordinates = (locationsList) => {
    const grouped = {}

    locationsList.forEach(location => {
      const key = `${location.latitude},${location.longitude}`

      if (!grouped[key]) {
        grouped[key] = {
          id: location.id,
          local: location.local,
          cidade: location.cidade,
          endereco: location.endereco,
          endereco_url: location.endereco_url,
          geocode_source: location.geocode_source,
          latitude: location.latitude,
          longitude: location.longitude,
          disciplinas: []
        }
      }

      grouped[key].disciplinas.push({
        disciplina: location.disciplina,
        atividade: location.atividade,
        especialidade: location.especialidade,
        coordenador: location.coordenador,
        preceptor: location.preceptor,
        estudante: location.estudante,
        periodo: location.periodo,
        periodo_original: location.periodo_original,
        turma: location.turma,
        categoria: location.categoria,
        dia: location.dia,
        turno: location.turno,
        ch_semanal: location.ch_semanal
      })
    })

    return Object.values(grouped)
  }

  // Aplicar filtros
  const filteredLocations = useMemo(() => {
    let filtered = locations

    if (selectedFilters.disciplina) {
      filtered = filtered.filter(loc => loc.disciplina === selectedFilters.disciplina)
    }
    if (selectedFilters.atividade) {
      filtered = filtered.filter(loc => loc.atividade === selectedFilters.atividade)
    }
    if (selectedFilters.especialidade) {
      filtered = filtered.filter(loc => loc.especialidade === selectedFilters.especialidade)
    }
    if (selectedFilters.periodo) {
      filtered = filtered.filter(loc => loc.periodo_original === selectedFilters.periodo)
    }
    if (selectedFilters.preceptor) {
      filtered = filtered.filter(loc => loc.preceptor === selectedFilters.preceptor)
    }
    if (selectedFilters.cidade) {
      filtered = filtered.filter(loc => loc.cidade === selectedFilters.cidade)
    }

    return groupLocationsByCoordinates(filtered)
  }, [selectedFilters, locations])

  const mapPoints = useMemo(
    () => filteredLocations.map(loc => [loc.latitude, loc.longitude]),
    [filteredLocations]
  )

  const totalAtividades = filteredLocations.reduce(
    (total, loc) => total + (loc.disciplinas?.length || 0), 0
  )
  const totalEstudantes = filteredLocations.reduce(
    (total, loc) => total + (loc.disciplinas?.reduce((sum, disc) => sum + (disc.estudante || 0), 0) || 0), 0
  )

  const handleFilterChange = (filterType, value) => {
    setSelectedFilters(prev => ({
      ...prev,
      [filterType]: value === 'all' ? '' : value
    }))
  }

  const clearFilters = () => {
    setSelectedFilters({
      disciplina: '',
      atividade: '',
      especialidade: '',
      periodo: '',
      preceptor: '',
      cidade: ''
    })
  }

  const toggleCardExpansion = (cardId) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev)
      if (newSet.has(cardId)) {
        newSet.delete(cardId)
      } else {
        newSet.add(cardId)
      }
      return newSet
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center bg-white rounded-2xl p-8 shadow-xl">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-200 border-t-faminas-blue mx-auto mb-6"></div>
          <p className="text-faminas-blue font-semibold text-lg">Carregando mapa...</p>
          <p className="text-gray-600 text-sm mt-2">Preparando dados dos estágios</p>
        </div>
      </div>
    )
  }

  const filterConfigs = [
    { key: 'disciplina', label: 'Disciplina', options: filters.disciplinas, placeholder: 'Todas as disciplinas' },
    { key: 'atividade', label: 'Atividade de campo', options: filters.atividades, placeholder: 'Núcleo e Internato' },
    { key: 'especialidade', label: 'Especialidade', options: filters.especialidades, placeholder: 'Todas as especialidades' },
    { key: 'periodo', label: 'Período', options: filters.periodos, placeholder: 'Todos os períodos' },
    { key: 'cidade', label: 'Cidade', options: filters.cidades, placeholder: 'Todas as cidades' },
    { key: 'preceptor', label: 'Preceptor', options: filters.preceptores, placeholder: 'Todos os preceptores' }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-xl border-b-4 border-faminas-pink">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <img
                src={faminasLogo}
                alt="Logo FAMINAS"
                className="h-18 w-auto object-contain drop-shadow-md"
              />
              <div>
                <h1 className="text-4xl font-bold text-faminas-blue tracking-tight">
                  Mapa Interativo de Estágios
                </h1>
                <p className="text-faminas-light mt-2 font-medium">
                  FAMINAS - Faculdade de Minas · Campos de estágio 2026.2
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="secondary" className="bg-faminas-blue text-white px-4 py-2 text-sm font-medium">
                <MapPin className="w-4 h-4 mr-2" />
                {filteredLocations.length} locais
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Painel de Filtros */}
          <div className="lg:col-span-1">
            <Card className="shadow-lg border-0 bg-white">
              <CardHeader className="bg-gradient-to-r from-faminas-blue to-faminas-light text-white rounded-t-lg">
                <CardTitle className="flex items-center text-lg">
                  <Users className="w-5 h-5 mr-3" />
                  Filtros
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                {filterConfigs.map(config => (
                  <div key={config.key}>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {config.label}
                    </label>
                    <Select
                      value={selectedFilters[config.key] || 'all'}
                      onValueChange={(value) => handleFilterChange(config.key, value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={config.placeholder} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">{config.placeholder}</SelectItem>
                        {config.options?.map(option => (
                          <SelectItem key={option} value={option}>
                            {option}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                ))}

                <Button
                  onClick={clearFilters}
                  variant="outline"
                  className="w-full border-faminas-pink text-faminas-pink hover:bg-faminas-pink hover:text-white"
                >
                  Limpar Filtros
                </Button>

                {/* Informações dos dados */}
                <div className="mt-6 p-5 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                      <span className="text-xs font-medium text-gray-600">REGISTROS</span>
                      <p className="text-lg font-bold text-gray-800 mt-1">{locations.length}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                      <span className="text-xs font-medium text-gray-600">LOCAIS</span>
                      <p className="text-lg font-bold text-gray-800 mt-1">{filteredLocations.length}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                      <span className="text-xs font-medium text-gray-600">ATIVIDADES</span>
                      <p className="text-lg font-bold text-gray-800 mt-1">{totalAtividades}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                      <span className="text-xs font-medium text-gray-600">ESTUDANTES</span>
                      <p className="text-lg font-bold text-gray-800 mt-1">{totalEstudantes}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Mapa */}
          <div className="lg:col-span-3">
            <Card className="shadow-lg border-0 overflow-hidden bg-white">
              <CardHeader className="bg-gradient-to-r from-faminas-light to-faminas-pink text-white">
                <CardTitle className="flex items-center text-lg">
                  <MapPin className="w-5 h-5 mr-3" />
                  Cenários de Prática - Minas Gerais
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="h-[600px] w-full">
                  <MapContainer
                    center={[-19.5, -44.0]}
                    zoom={7}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />

                    <FitBounds points={mapPoints} />

                    {filteredLocations.map((location) => (
                      <Marker
                        key={`${location.latitude}-${location.longitude}`}
                        position={[location.latitude, location.longitude]}
                      >
                        <Popup maxWidth={450} className="custom-popup">
                          <div className="p-4">
                            <h3 className="font-bold text-faminas-blue mb-1 text-lg border-b pb-2">
                              {location.local}
                            </h3>
                            <p className="text-xs text-gray-500 mb-3">{location.cidade}</p>
                            <div className="space-y-3">
                              <div className="bg-blue-50 p-3 rounded-lg">
                                <p className="text-sm"><strong>📍 Endereço:</strong> {location.endereco}</p>
                                {location.endereco_url && (
                                  <p className="text-sm mt-1">
                                    <a href={location.endereco_url} target="_blank" rel="noreferrer" className="text-faminas-pink underline">
                                      Ver ficha do estabelecimento
                                    </a>
                                  </p>
                                )}
                                {location.geocode_source === 'cidade' && (
                                  <p className="text-xs text-amber-600 mt-1">⚠️ Localização aproximada (centro da cidade)</p>
                                )}
                              </div>

                              {location.disciplinas && location.disciplinas.length > 0 && (
                                <div>
                                  <div className="flex items-center gap-2 mb-3">
                                    <strong className="text-gray-800">📚 Atividades</strong>
                                    <Badge variant="outline" className="bg-faminas-pink text-white border-faminas-pink">
                                      {location.disciplinas.length}
                                    </Badge>
                                  </div>

                                  <div className="scroll-container">
                                    <div className="max-h-64 overflow-y-auto space-y-2 pr-2 popup-scroll">
                                      {location.disciplinas.map((disciplinaInfo, index) => {
                                        const cardId = `${location.latitude}-${location.longitude}-${index}`
                                        const isExpanded = expandedCards.has(cardId)

                                        return (
                                          <div key={index} className="disciplina-card border border-gray-200 bg-white rounded-lg shadow-sm overflow-hidden">
                                            <div
                                              className="p-2 cursor-pointer hover:bg-gray-50 transition-colors"
                                              onClick={() => toggleCardExpansion(cardId)}
                                            >
                                              <div className="flex items-center justify-between mb-1 gap-2">
                                                <div className="flex flex-wrap items-center gap-1">
                                                  <Badge variant="secondary" className="bg-faminas-light text-white font-medium text-xs">
                                                    {disciplinaInfo.disciplina}
                                                  </Badge>
                                                  {disciplinaInfo.atividade && (
                                                    <Badge variant="outline" className="text-[10px] border-faminas-blue text-faminas-blue">
                                                      {disciplinaInfo.atividade}
                                                    </Badge>
                                                  )}
                                                </div>
                                                <div className="flex items-center space-x-2 shrink-0">
                                                  {disciplinaInfo.periodo_original && (
                                                    <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                                                      {disciplinaInfo.periodo_original}
                                                    </span>
                                                  )}
                                                  {isExpanded ? (
                                                    <ChevronUp className="w-4 h-4 text-gray-400" />
                                                  ) : (
                                                    <ChevronDown className="w-4 h-4 text-gray-400" />
                                                  )}
                                                </div>
                                              </div>
                                              <div className="text-xs text-gray-700 space-y-1">
                                                {disciplinaInfo.especialidade && (
                                                  <p className="text-gray-600"><strong>🩺</strong> {disciplinaInfo.especialidade}</p>
                                                )}
                                                <p className="text-gray-600"><strong>👨‍⚕️ Preceptor:</strong> {disciplinaInfo.preceptor}</p>
                                                <div className="flex items-center justify-between text-xs">
                                                  <div className="flex items-center space-x-3">
                                                    {disciplinaInfo.turma && (
                                                      <span><strong>👥</strong> Turma {disciplinaInfo.turma}</span>
                                                    )}
                                                    {disciplinaInfo.turno && (
                                                      <span><strong>🕐</strong> {disciplinaInfo.turno}</span>
                                                    )}
                                                  </div>
                                                  {disciplinaInfo.estudante > 0 && (
                                                    <div className="text-faminas-blue font-medium">
                                                      <strong>🎓</strong> {disciplinaInfo.estudante} alunos
                                                    </div>
                                                  )}
                                                </div>
                                              </div>
                                            </div>

                                            {isExpanded && (
                                              <div className="px-2 pb-2 border-t border-gray-100 bg-gray-50">
                                                <div className="pt-2 text-xs text-gray-600 space-y-1">
                                                  {disciplinaInfo.coordenador && (
                                                    <p><strong>Coordenador(a) do núcleo/internato:</strong> {disciplinaInfo.coordenador}</p>
                                                  )}
                                                  {disciplinaInfo.dia && (
                                                    <p><strong>Dia da semana:</strong> {disciplinaInfo.dia}</p>
                                                  )}
                                                  {disciplinaInfo.ch_semanal && (
                                                    <p><strong>Carga horária semanal:</strong> {disciplinaInfo.ch_semanal}h</p>
                                                  )}
                                                  {disciplinaInfo.estudante > 0 && (
                                                    <p><strong>Quantidade de alunos:</strong> {disciplinaInfo.estudante}</p>
                                                  )}
                                                  {disciplinaInfo.categoria && (
                                                    <p><strong>Categoria:</strong> {disciplinaInfo.categoria}</p>
                                                  )}
                                                </div>
                                              </div>
                                            )}
                                          </div>
                                        )
                                      })}
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </Popup>
                      </Marker>
                    ))}
                  </MapContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
