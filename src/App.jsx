import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { MapPin, Users, GraduationCap, Clock } from 'lucide-react'
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

function App() {
  const [locations, setLocations] = useState([])
  const [filteredLocations, setFilteredLocations] = useState([])
  const [filters, setFilters] = useState({})
  const [selectedFilters, setSelectedFilters] = useState({
    disciplina: '',
    periodo: '',
    preceptor: ''
  })
  const [loading, setLoading] = useState(true)

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
        // Inicializar com locais agrupados
        const groupedLocations = groupLocationsByCoordinates(locationsData)
        setFilteredLocations(groupedLocations)
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
          endereco: location.endereco,
          latitude: location.latitude,
          longitude: location.longitude,
          disciplinas: []
        }
      }
      
      grouped[key].disciplinas.push({
        disciplina: location.disciplina,
        preceptor: location.preceptor,
        estudante: location.estudante,
        periodo_original: location.periodo_original,
        turma: location.turma,
        categoria: location.categoria,
        turno: location.turno
      })
    })
    
    return Object.values(grouped)
  }

  // Aplicar filtros
  useEffect(() => {
    let filtered = locations

    if (selectedFilters.disciplina) {
      filtered = filtered.filter(loc => loc.disciplina === selectedFilters.disciplina)
    }
    
    if (selectedFilters.periodo) {
      filtered = filtered.filter(loc => loc.periodo_original === selectedFilters.periodo)
    }
    
    if (selectedFilters.preceptor) {
      filtered = filtered.filter(loc => loc.preceptor === selectedFilters.preceptor)
    }

    // Agrupar localizações por coordenadas
    const groupedLocations = groupLocationsByCoordinates(filtered)
    setFilteredLocations(groupedLocations)
  }, [selectedFilters, locations])

  const handleFilterChange = (filterType, value) => {
    setSelectedFilters(prev => ({
      ...prev,
      [filterType]: value === 'all' ? '' : value
    }))
  }

  const clearFilters = () => {
    setSelectedFilters({
      disciplina: '',
      periodo: '',
      preceptor: ''
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-faminas-blue mx-auto mb-4"></div>
          <p className="text-faminas-blue font-medium">Carregando mapa...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg border-b-4 border-faminas-pink">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <img 
                src={faminasLogo} 
                alt="Logo FAMINAS" 
                className="h-16 w-auto object-contain"
              />
              <div>
                <h1 className="text-3xl font-bold text-faminas-blue">
                  Mapa Interativo de Estágios
                </h1>
                <p className="text-faminas-light mt-1">
                  FAMINAS - Faculdade de Minas
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="secondary" className="bg-faminas-light text-white">
                <MapPin className="w-4 h-4 mr-1" />
                {filteredLocations.length} locais
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Painel de Filtros */}
          <div className="lg:col-span-1">
            <Card className="shadow-lg border-0">
              <CardHeader className="bg-faminas-blue text-white rounded-t-lg">
                <CardTitle className="flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Filtros
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                {/* Filtro Disciplina */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Disciplina
                  </label>
                  <Select 
                    value={selectedFilters.disciplina || 'all'} 
                    onValueChange={(value) => handleFilterChange('disciplina', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Todas as disciplinas" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas as disciplinas</SelectItem>
                      {filters.disciplinas?.map(disciplina => (
                        <SelectItem key={disciplina} value={disciplina}>
                          {disciplina}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Filtro Período */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Período
                  </label>
                  <Select 
                    value={selectedFilters.periodo || 'all'} 
                    onValueChange={(value) => handleFilterChange('periodo', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Todos os períodos" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos os períodos</SelectItem>
                      {filters.periodos?.map(periodo => (
                        <SelectItem key={periodo} value={periodo}>
                          {periodo}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Filtro Preceptor */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preceptor
                  </label>
                  <Select 
                    value={selectedFilters.preceptor || 'all'} 
                    onValueChange={(value) => handleFilterChange('preceptor', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Todos os preceptores" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos os preceptores</SelectItem>
                      {filters.preceptores?.map(preceptor => (
                        <SelectItem key={preceptor} value={preceptor}>
                          {preceptor}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={clearFilters} 
                  variant="outline" 
                  className="w-full border-faminas-pink text-faminas-pink hover:bg-faminas-pink hover:text-white"
                >
                  Limpar Filtros
                </Button>

                {/* Estatísticas */}
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-3">Estatísticas</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Total de registros:</span>
                      <span className="font-medium">{locations.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Locais únicos:</span>
                      <span className="font-medium text-faminas-pink">{filteredLocations.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total disciplinas:</span>
                      <span className="font-medium text-faminas-blue">
                        {filteredLocations.reduce((total, loc) => total + (loc.disciplinas?.length || 0), 0)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Disciplinas:</span>
                      <span className="font-medium">{filters.disciplinas?.length || 0}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Mapa */}
          <div className="lg:col-span-3">
            <Card className="shadow-lg border-0 overflow-hidden">
              <CardHeader className="bg-faminas-light text-white">
                <CardTitle className="flex items-center">
                  <MapPin className="w-5 h-5 mr-2" />
                  Cenários de Prática em Belo Horizonte
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="h-[600px] w-full">
                  <MapContainer
                    center={[-19.9167, -43.9345]} // Centro de Belo Horizonte
                    zoom={11}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                    
                    {filteredLocations.map((location) => (
                      <Marker
                        key={`${location.latitude}-${location.longitude}`}
                        position={[location.latitude, location.longitude]}
                      >
                        <Popup maxWidth={450} className="custom-popup">
                          <div className="p-4">
                            <h3 className="font-bold text-faminas-blue mb-3 text-lg border-b pb-2">
                              {location.local}
                            </h3>
                            <div className="space-y-3">
                              <div className="bg-blue-50 p-3 rounded-lg">
                                <p className="text-sm"><strong>📍 Endereço:</strong> {location.endereco}</p>
                              </div>
                              
                              {/* Exibir múltiplas disciplinas com scroll */}
                              {location.disciplinas && location.disciplinas.length > 0 && (
                                <div>
                                  <div className="flex items-center gap-2 mb-3">
                                    <strong className="text-gray-800">📚 Disciplinas</strong>
                                    <Badge variant="outline" className="bg-faminas-pink text-white border-faminas-pink">
                                      {location.disciplinas.length}
                                    </Badge>
                                  </div>
                                  
                                  {/* Container com scroll */}
                                  <div className="scroll-container">
                                    <div className="max-h-64 overflow-y-auto space-y-3 pr-2 popup-scroll">
                                      {location.disciplinas.map((disciplinaInfo, index) => (
                                        <div key={index} className="disciplina-card border border-gray-200 bg-white p-3 rounded-lg shadow-sm">
                                        <div className="flex items-center justify-between mb-2">
                                          <Badge variant="secondary" className="bg-faminas-light text-white font-medium">
                                            {disciplinaInfo.disciplina}
                                          </Badge>
                                          <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                                            {disciplinaInfo.periodo_original}
                                          </span>
                                        </div>
                                        <div className="text-xs text-gray-700 space-y-1.5 grid grid-cols-2 gap-2">
                                          <div>
                                            <p><strong>👨‍⚕️ Preceptor:</strong></p>
                                            <p className="text-gray-600 truncate">{disciplinaInfo.preceptor}</p>
                                          </div>
                                          <div>
                                            <p><strong>🎓 Estudante:</strong> {disciplinaInfo.estudante}</p>
                                            <p><strong>🕐 Turno:</strong> {disciplinaInfo.turno}</p>
                                          </div>
                                          {disciplinaInfo.turma && (
                                            <div className="col-span-2">
                                              <p><strong>👥 Turma:</strong> {disciplinaInfo.turma}</p>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                      ))}
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

