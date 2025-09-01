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
        setFilteredLocations(locationsData)
        setFilters(filtersData)
        setLoading(false)
      } catch (error) {
        console.error('Erro ao carregar dados:', error)
        setLoading(false)
      }
    }
    
    loadData()
  }, [])

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

    setFilteredLocations(filtered)
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
            <div>
              <h1 className="text-3xl font-bold text-faminas-blue">
                Mapa Interativo de Estágios
              </h1>
              <p className="text-faminas-light mt-1">
                FAMINAS - Faculdade de Minas
              </p>
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
                      <span>Total de locais:</span>
                      <span className="font-medium">{locations.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Locais filtrados:</span>
                      <span className="font-medium text-faminas-pink">{filteredLocations.length}</span>
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
                  Locais de Estágio em Belo Horizonte
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
                        key={location.id}
                        position={[location.latitude, location.longitude]}
                      >
                        <Popup maxWidth={300} className="custom-popup">
                          <div className="p-2">
                            <h3 className="font-bold text-faminas-blue mb-2">
                              {location.local}
                            </h3>
                            <div className="space-y-1 text-sm">
                              <p><strong>Endereço:</strong> {location.endereco}</p>
                              <p><strong>Disciplina:</strong> 
                                <Badge variant="secondary" className="ml-1 bg-faminas-light text-white">
                                  {location.disciplina}
                                </Badge>
                              </p>
                              <p><strong>Período:</strong> {location.periodo_original}</p>
                              <p><strong>Preceptor:</strong> {location.preceptor}</p>
                              <p><strong>Estudante:</strong> {location.estudante}</p>
                              <p><strong>Turno:</strong> {location.turno}</p>
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

