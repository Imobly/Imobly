"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MapPin, Bed, Bath, Car, Edit, Trash2, ChevronLeft, ChevronRight } from "lucide-react"
import Image from "next/image"
import { Property } from "@/lib/types/property"
import { useTenants } from "@/lib/hooks/useTenants"
import { PropertyDetailDialog } from "./property-detail-dialog"

interface PropertyCardProps {
  property: Property
  onEdit: (property: Property) => void
  onDelete: (id: number) => void
}

const statusConfig = {
  occupied: { label: "Ocupado", className: "bg-green-100 text-green-800" },
  vacant: { label: "Vago", className: "bg-gray-100 text-gray-800" },
  maintenance: { label: "Manutenção", className: "bg-orange-100 text-orange-800" },
}

const typeConfig = {
  apartment: "Apartamento",
  house: "Casa",
  commercial: "Comercial",
}

export function PropertyCard({ property, onEdit, onDelete }: PropertyCardProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const { tenants } = useTenants()
  const tenantName = property.tenant_id ? tenants.find(t => t.id === property.tenant_id)?.name : undefined
  
  // Construir URLs completas das imagens
  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:8000'
  const images = property.images && property.images.length > 0 
    ? property.images.map(img => img.startsWith('http') ? img : `${baseUrl}${img}`)
    : ["/placeholder.svg"]

  const handleDelete = () => {
    onDelete(property.id)
  }

  const handlePreviousImage = (e: React.MouseEvent) => {
    e.stopPropagation()
    setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1))
  }

  const handleNextImage = (e: React.MouseEvent) => {
    e.stopPropagation()
    setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1))
  }

  return (
    <>
      <Card className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setShowDetailDialog(true)}>
        <div className="relative h-48 group">
        <Image 
          src={images[currentImageIndex]} 
          alt={property.name} 
          fill 
          className="object-cover" 
        />
        
        {/* Navigation Arrows */}
        {images.length > 1 && (
          <>
            <Button
              variant="secondary"
              size="sm"
              className="absolute left-2 top-1/2 -translate-y-1/2 h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={handlePreviousImage}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="secondary"
              size="sm"
              className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={handleNextImage}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
            
            {/* Image Indicators */}
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
              {images.map((_, index) => (
                <div
                  key={index}
                  className={`h-1.5 rounded-full transition-all ${
                    index === currentImageIndex 
                      ? 'w-4 bg-white' 
                      : 'w-1.5 bg-white/50'
                  }`}
                />
              ))}
            </div>
          </>
        )}

        <div className="absolute top-2 right-2 flex gap-2">
          <Button 
            variant="secondary" 
            size="sm" 
            className="h-8 w-8 p-0"
            onClick={(e) => {
              e.stopPropagation()
              onEdit(property)
            }}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button 
            variant="destructive" 
            size="sm" 
            className="h-8 w-8 p-0"
            onClick={(e) => {
              e.stopPropagation()
              handleDelete()
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
        <div className="absolute top-2 left-2">
          <Badge variant="secondary" className={statusConfig[property.status as keyof typeof statusConfig].className}>
            {statusConfig[property.status as keyof typeof statusConfig].label}
          </Badge>
        </div>
      </div>

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-lg">{property.name}</h3>
            <div className="flex items-center text-sm text-muted-foreground mt-1">
              <MapPin className="mr-1 h-3 w-3" />
              {property.address}, {property.neighborhood}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Tipo:</span>
            <span>{typeConfig[property.type as keyof typeof typeConfig]}</span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Área:</span>
            <span>{property.area}m²</span>
          </div>

          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
            {property.bedrooms > 0 && (
              <div className="flex items-center">
                <Bed className="mr-1 h-3 w-3" />
                {property.bedrooms}
              </div>
            )}
            <div className="flex items-center">
              <Bath className="mr-1 h-3 w-3" />
              {property.bathrooms}
            </div>
            {property.parkingSpaces > 0 && (
              <div className="flex items-center">
                <Car className="mr-1 h-3 w-3" />
                {property.parkingSpaces}
              </div>
            )}
          </div>

          {tenantName && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Inquilino:</span>
              <span>{tenantName}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-lg font-bold">R$ {property.rent.toLocaleString("pt-BR")}</span>
            <span className="text-xs text-muted-foreground">/mês</span>
          </div>
        </div>
      </CardContent>
    </Card>
    
    <PropertyDetailDialog
      open={showDetailDialog}
      onOpenChange={setShowDetailDialog}
      property={property}
      onEdit={onEdit}
      onDelete={onDelete}
    />
    </>
  )
}
