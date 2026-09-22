"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusDot, type StatusTone } from "@/components/ui/status-dot"
import { MapPin, Bed, Bath, Car, Edit, Trash2, ChevronLeft, ChevronRight, Building2 } from "lucide-react"
import Image from "next/image"
import { Property } from "@/lib/types/property"
import { useTenants } from "@/lib/hooks/useTenants"
import { PropertyDetailDialog } from "./property-detail-dialog"
import { formatCurrency } from '@/lib/utils/format'

interface PropertyCardProps {
  property: Property
  onEdit: (property: Property) => void
  onDelete: (id: number) => void
}

const statusConfig: Record<string, { label: string; tone: StatusTone }> = {
  occupied: { label: "Ocupado", tone: "brand" },
  vacant: { label: "Vago", tone: "info" },
  maintenance: { label: "Manutenção", tone: "warning" },
  inactive: { label: "Inativo", tone: "neutral" },
}

const typeConfig = {
  apartment: "Apartamento",
  house: "Casa",
  commercial: "Comercial",
  studio: "Studio",
}

export function PropertyCard({ property, onEdit, onDelete }: PropertyCardProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const { tenants } = useTenants()
  const tenantName = property.tenant_id ? tenants.find(t => t.id === property.tenant_id)?.name : undefined

  // Construir URLs completas das imagens.
  //
  // As fotos vêm do Supabase Storage com URL absoluta, tratada pelo
  // startsWith('http') abaixo; o backend não serve mais /uploads (o mount foi
  // removido por expor documentos sem autenticação). O prefixo só cobre um
  // path relativo legado — e fica relativo ao próprio frontend, sem apontar
  // para localhost:8000, porta que outro projeto pode estar ocupando.
  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') ?? ''
  const images = (property.images ?? []).map(img =>
    img.startsWith('http') ? img : `${baseUrl}${img}`
  )
  const hasImages = images.length > 0

  const status = statusConfig[property.status as keyof typeof statusConfig] ?? statusConfig.vacant

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
      <Card
        className="group hover:border-brand-300 cursor-pointer gap-0 overflow-hidden py-0 shadow-none transition-colors hover:shadow-md"
        onClick={() => setShowDetailDialog(true)}
      >
        <div className="relative h-44">
          {hasImages ? (
            <Image
              src={images[currentImageIndex]}
              alt={property.name}
              fill
              className="object-cover"
            />
          ) : (
            /* Sem foto, uma chapa em papel-quadriculado da própria marca. O
               placeholder cinza anterior dominava o card e fazia a carteira
               inteira parecer vazia. */
            <div
              className="bg-brand-50 flex h-full items-center justify-center"
              style={{
                backgroundImage:
                  'repeating-linear-gradient(0deg, rgba(9,91,189,.07) 0 1px, transparent 1px 28px), repeating-linear-gradient(90deg, rgba(9,91,189,.07) 0 1px, transparent 1px 28px)',
              }}
            >
              <Building2 className="text-brand-300 h-14 w-14" strokeWidth={1.1} aria-hidden />
            </div>
          )}

          {/* Navigation Arrows */}
          {images.length > 1 && (
            <>
              <Button
                variant="secondary"
                size="icon"
                className="absolute top-1/2 left-2 size-8 -translate-y-1/2 bg-white/90 opacity-0 transition-opacity group-hover:opacity-100"
                onClick={handlePreviousImage}
                aria-label="Foto anterior"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="secondary"
                size="icon"
                className="absolute top-1/2 right-2 size-8 -translate-y-1/2 bg-white/90 opacity-0 transition-opacity group-hover:opacity-100"
                onClick={handleNextImage}
                aria-label="Próxima foto"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>

              {/* Image Indicators */}
              <div className="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1">
                {images.map((_, index) => (
                  <div
                    key={index}
                    className={`h-1.5 rounded-full transition-all ${
                      index === currentImageIndex ? 'w-4 bg-white' : 'w-1.5 bg-white/50'
                    }`}
                  />
                ))}
              </div>
            </>
          )}

          {/* Ações: só no hover. Antes um botão vermelho cheio de excluir ficava
              aceso em todos os cards da grade ao mesmo tempo. */}
          <div className="absolute top-3 right-3 flex gap-2 opacity-0 transition-opacity group-focus-within:opacity-100 group-hover:opacity-100">
            <Button
              variant="outline"
              size="icon"
              className="size-9 bg-white"
              aria-label={`Editar ${property.name}`}
              onClick={(e) => {
                e.stopPropagation()
                onEdit(property)
              }}
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="text-critical-strong border-critical-soft hover:bg-critical-soft size-9 bg-white"
              aria-label={`Excluir ${property.name}`}
              onClick={(e) => {
                e.stopPropagation()
                handleDelete()
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>

          {/* Acesso defensivo: um status fora do mapa (ex.: vindo direto da
              API antes de um novo valor ser cadastrado aqui) não pode
              derrubar o card inteiro. */}
          <div className="absolute top-3 left-3 rounded-full bg-white px-3 py-1.5 shadow-sm">
            <StatusDot tone={status.tone}>{status.label}</StatusDot>
          </div>
        </div>

        <div className="flex flex-col gap-3.5 p-5">
          <div>
            <h3 className="leading-snug font-bold">{property.name}</h3>
            <p className="text-muted-foreground mt-1 flex items-center gap-1.5 text-sm">
              <MapPin className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{property.address}, {property.neighborhood}</span>
            </p>
          </div>

          <div className="bg-hairline h-px" />

          {/* Tipo, área e cômodos numa linha só: são qualificadores do imóvel,
              não três fatos que merecem uma linha cada. */}
          <div className="text-foreground/80 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
            <span className="font-semibold">
              {typeConfig[property.type as keyof typeof typeConfig] ?? property.type}
            </span>
            <span className="text-neutral-track">·</span>
            <span>{property.area}m²</span>
            {property.bedrooms > 0 && (
              <>
                <span className="text-neutral-track">·</span>
                <span className="flex items-center gap-1">
                  <Bed className="text-muted-foreground h-4 w-4" />
                  {property.bedrooms}
                </span>
              </>
            )}
            <span className="flex items-center gap-1">
              <Bath className="text-muted-foreground h-4 w-4" />
              {property.bathrooms}
            </span>
            {property.parkingSpaces > 0 && (
              <span className="flex items-center gap-1">
                <Car className="text-muted-foreground h-4 w-4" />
                {property.parkingSpaces}
              </span>
            )}
          </div>

          {tenantName && (
            <p className="text-muted-foreground truncate text-sm">
              Inquilino: <span className="text-foreground font-medium">{tenantName}</span>
            </p>
          )}

          <div className="bg-hairline h-px" />

          <div>
            <p className="text-muted-foreground text-xs">Aluguel</p>
            <p className="flex items-baseline gap-1.5">
              <span className="font-display text-xl font-bold tracking-tight">
                {formatCurrency(property.rent)}
              </span>
              <span className="text-muted-foreground text-xs">/mês</span>
            </p>
          </div>
        </div>
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
