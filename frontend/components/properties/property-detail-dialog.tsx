"use client"

import React, { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ChevronLeft, ChevronRight, MapPin, Bed, Bath, Car, Edit, Trash2 } from "lucide-react"
import { Property } from "@/lib/types/property"
import Image from "next/image"
import { useTenants } from "@/lib/hooks/useTenants"

interface PropertyDetailDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
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

export function PropertyDetailDialog({
  open,
  onOpenChange,
  property,
  onEdit,
  onDelete,
}: PropertyDetailDialogProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const { tenants } = useTenants()
  const tenantName = property.tenant_id ? tenants.find(t => t.id === property.tenant_id)?.name : undefined

  // Construir URLs completas das imagens
  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") || "http://localhost:8000"
  const images = property.images && property.images.length > 0
    ? property.images.map(img => {
        if (img.startsWith("http") || img.startsWith("blob:") || img.startsWith("/")) {
          return img
        }
        return `${baseUrl}${img.startsWith("/") ? img : "/" + img}`
      })
    : ["/placeholder.svg"]

  const handlePreviousImage = () => {
    setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1))
  }

  const handleNextImage = () => {
    setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1))
  }

  const handleDelete = () => {
    onDelete(property.id)
    onOpenChange(false)
  }

  const handleEdit = () => {
    onEdit(property)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="!max-w-[85vw] w-[85vw] h-[85vh] p-0 overflow-hidden" showCloseButton={false}>
        <button
          onClick={() => onOpenChange(false)}
          className="absolute top-4 right-4 z-50 rounded-full bg-black/50 p-2 text-white hover:bg-black/70 transition-colors"
        >
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M11.7816 4.03157C12.0062 3.80702 12.0062 3.44295 11.7816 3.2184C11.5571 2.99385 11.193 2.99385 10.9685 3.2184L7.50005 6.68682L4.03164 3.2184C3.80708 2.99385 3.44301 2.99385 3.21846 3.2184C2.99391 3.44295 2.99391 3.80702 3.21846 4.03157L6.68688 7.49999L3.21846 10.9684C2.99391 11.193 2.99391 11.557 3.21846 11.7816C3.44301 12.0061 3.80708 12.0061 4.03164 11.7816L7.50005 8.31316L10.9685 11.7816C11.193 12.0061 11.5571 12.0061 11.7816 11.7816C12.0062 11.557 12.0062 11.193 11.7816 10.9684L8.31322 7.49999L11.7816 4.03157Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
          </svg>
        </button>
        <div className="flex h-full w-full">
          {/* Coluna Esquerda - Galeria de Imagens (55%) */}
          <div className="relative bg-black w-[55%] h-full flex items-center justify-center overflow-hidden flex-shrink-0">
            <div className="relative w-full h-full">
              <Image
                src={images[currentImageIndex]}
                alt={`${property.name} - Foto ${currentImageIndex + 1}`}
                fill
                className="object-cover"
                priority
              />
            </div>

            {images.length > 1 && (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  className="absolute left-4 top-1/2 -translate-y-1/2 h-9 w-9 p-0 bg-white/90 hover:bg-white"
                  onClick={handlePreviousImage}
                >
                  <ChevronLeft className="h-5 w-5" />
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  className="absolute right-4 top-1/2 -translate-y-1/2 h-9 w-9 p-0 bg-white/90 hover:bg-white"
                  onClick={handleNextImage}
                >
                  <ChevronRight className="h-5 w-5" />
                </Button>

                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                  {images.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentImageIndex(index)}
                      className={`h-2 rounded-full transition-all ${index === currentImageIndex ? "w-8 bg-white" : "w-2 bg-white/50 hover:bg-white/75"}`}
                    />
                  ))}
                </div>

                <div className="absolute top-4 right-4 px-3 py-1 bg-black/60 text-white text-sm rounded-full">
                  {currentImageIndex + 1} / {images.length}
                </div>
              </>
            )}
          </div>

          {/* Coluna Direita - Informações (45%) */}
          <div className="flex flex-col w-[45%] max-h-full bg-white overflow-hidden flex-shrink-0">
            <DialogHeader className="px-6 pt-6 pb-4 border-b bg-white flex-shrink-0">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <DialogTitle className="text-2xl mb-2">{property.name}</DialogTitle>
                  <div className="flex items-start text-muted-foreground">
                    <MapPin className="mr-1 h-4 w-4 shrink-0 mt-0.5" />
                    <span className="text-sm">
                      {property.address}, {property.neighborhood} - {property.city}/{property.state}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-3 flex-wrap">
                <Badge className={statusConfig[property.status as keyof typeof statusConfig].className}>
                  {statusConfig[property.status as keyof typeof statusConfig].label}
                </Badge>
                <Badge variant="outline">{typeConfig[property.type as keyof typeof typeConfig]}</Badge>
              </div>
            </DialogHeader>

            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100 min-h-0">
              <div className="bg-primary/5 p-4 rounded-lg">
                <p className="text-sm text-muted-foreground mb-1">Valor do Aluguel</p>
                <p className="text-3xl font-bold text-primary">
                  R$ {property.rent.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  <span className="text-sm font-normal text-muted-foreground ml-1">/mês</span>
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-base mb-3">Características</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Bed className="h-5 w-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs text-muted-foreground">Quartos</p>
                      <p className="text-base font-medium">{property.bedrooms}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Bath className="h-5 w-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs text-muted-foreground">Banheiros</p>
                      <p className="text-base font-medium">{property.bathrooms}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Car className="h-5 w-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs text-muted-foreground">Vagas</p>
                      <p className="text-base font-medium">{property.parkingSpaces}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-primary text-sm font-semibold">m²</span>
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs text-muted-foreground">Área</p>
                      <p className="text-base font-medium">{property.area}m²</p>
                    </div>
                  </div>
                </div>
              </div>

              {tenantName && (
                <div>
                  <h3 className="font-semibold text-base mb-2">Inquilino Atual</h3>
                  <p className="text-sm">{tenantName}</p>
                </div>
              )}

              <div>
                <h3 className="font-semibold text-base mb-2">Descrição</h3>
                <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                  {property.description || "Nenhuma descrição disponível"}
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-base mb-2">Endereço Completo</h3>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p>{property.address}</p>
                  <p>{property.neighborhood}</p>
                  <p>
                    {property.city} - {property.state}
                  </p>
                  {property.zipCode && <p>CEP: {property.zipCode}</p>}
                </div>
              </div>
            </div>

            <div className="border-t bg-white px-6 py-4 flex gap-3 flex-shrink-0">
              <Button className="flex-1" onClick={handleEdit}>
                <Edit className="h-4 w-4 mr-2" />
                Editar
              </Button>
              <Button variant="destructive" className="flex-1" onClick={handleDelete}>
                <Trash2 className="h-4 w-4 mr-2" />
                Excluir
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
