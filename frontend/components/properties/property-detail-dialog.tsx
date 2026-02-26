"use client"

import React, { useState, useCallback } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  ChevronLeft,
  ChevronRight,
  MapPin,
  Bed,
  Bath,
  Car,
  Edit,
  Trash2,
  X,
  User,
} from "lucide-react"
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

const statusConfig: Record<string, { label: string; className: string }> = {
  occupied: { label: "Ocupado", className: "bg-emerald-100 text-emerald-700 border-emerald-200" },
  vacant: { label: "Vago", className: "bg-slate-100 text-slate-700 border-slate-200" },
  maintenance: { label: "Manutenção", className: "bg-amber-100 text-amber-700 border-amber-200" },
}

const typeConfig: Record<string, string> = {
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
  const tenantName = property.tenant_id
    ? tenants.find((t) => t.id === property.tenant_id)?.name
    : undefined

  // Build full image URLs
  const baseUrl =
    process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") || "http://localhost:8000"
  const images =
    property.images && property.images.length > 0
      ? property.images.map((img) => {
          if (img.startsWith("http") || img.startsWith("blob:") || img.startsWith("/")) return img
          return `${baseUrl}/${img}`
        })
      : ["/placeholder.svg"]

  const handlePreviousImage = useCallback(() => {
    setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1))
  }, [images.length])

  const handleNextImage = useCallback(() => {
    setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1))
  }, [images.length])

  const handleDelete = () => {
    onDelete(property.id)
    onOpenChange(false)
  }

  const handleEdit = () => {
    onEdit(property)
    onOpenChange(false)
  }

  const status = statusConfig[property.status] ?? statusConfig.vacant
  const typeName = typeConfig[property.type] ?? property.type

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="!max-w-5xl w-[95vw] md:w-[85vw] max-h-[90vh] p-0 overflow-hidden rounded-2xl shadow-2xl border-0"
        showCloseButton={false}
      >
        {/* Close button */}
        <button
          onClick={() => onOpenChange(false)}
          className="absolute top-3 right-3 z-50 rounded-full bg-black/40 backdrop-blur-sm p-1.5 text-white hover:bg-black/60 transition-all"
          aria-label="Fechar"
        >
          <X className="h-4 w-4" />
        </button>

        {/* ── Main layout: vertical on mobile, horizontal on desktop ── */}
        <div className="flex flex-col md:flex-row h-full max-h-[90vh]">

          {/* ────────────────── LEFT: Image Gallery ────────────────── */}
          <div className="relative bg-slate-900 w-full md:w-[55%] h-[240px] sm:h-[300px] md:h-auto md:min-h-[500px] flex-shrink-0 overflow-hidden">
            <div className="relative w-full h-full">
              <Image
                src={images[currentImageIndex]}
                alt={`${property.name} - Foto ${currentImageIndex + 1}`}
                fill
                sizes="(max-width: 768px) 100vw, 55vw"
                className="object-cover"
                priority
              />

              {/* Gradient overlay for indicators */}
              <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/50 to-transparent pointer-events-none" />
            </div>

            {images.length > 1 && (
              <>
                {/* Navigation arrows */}
                <button
                  onClick={handlePreviousImage}
                  className="absolute left-3 top-1/2 -translate-y-1/2 h-9 w-9 rounded-full bg-white/90 hover:bg-white shadow-lg flex items-center justify-center transition-all hover:scale-105"
                  aria-label="Imagem anterior"
                >
                  <ChevronLeft className="h-5 w-5 text-slate-700" />
                </button>
                <button
                  onClick={handleNextImage}
                  className="absolute right-3 top-1/2 -translate-y-1/2 h-9 w-9 rounded-full bg-white/90 hover:bg-white shadow-lg flex items-center justify-center transition-all hover:scale-105"
                  aria-label="Próxima imagem"
                >
                  <ChevronRight className="h-5 w-5 text-slate-700" />
                </button>

                {/* Dot indicators */}
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5">
                  {images.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentImageIndex(index)}
                      className={`rounded-full transition-all duration-300 ${
                        index === currentImageIndex
                          ? "w-6 h-2 bg-white"
                          : "w-2 h-2 bg-white/50 hover:bg-white/75"
                      }`}
                      aria-label={`Ir para imagem ${index + 1}`}
                    />
                  ))}
                </div>

                {/* Image counter badge */}
                <div className="absolute top-3 left-3 px-2.5 py-1 bg-black/50 backdrop-blur-sm text-white text-xs font-medium rounded-full">
                  {currentImageIndex + 1} / {images.length}
                </div>
              </>
            )}
          </div>

          {/* ────────────────── RIGHT: Info Panel ────────────────── */}
          <div className="flex flex-col w-full md:w-[45%] max-h-[calc(90vh-240px)] sm:max-h-[calc(90vh-300px)] md:max-h-[90vh] bg-white">

            {/* Header — sticky */}
            <DialogHeader className="px-5 md:px-6 pt-5 pb-4 border-b border-slate-100 flex-shrink-0">
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                <Badge className={`text-xs font-medium border ${status.className}`}>
                  {status.label}
                </Badge>
                <Badge variant="outline" className="text-xs font-medium">
                  {typeName}
                </Badge>
              </div>
              <DialogTitle className="text-xl md:text-2xl font-bold text-slate-900 leading-tight">
                {property.name}
              </DialogTitle>
              <div className="flex items-start text-slate-500 mt-1.5">
                <MapPin className="mr-1.5 h-3.5 w-3.5 shrink-0 mt-0.5" />
                <span className="text-sm leading-snug">
                  {property.address}, {property.neighborhood} - {property.city}/{property.state}
                </span>
              </div>
            </DialogHeader>

            {/* Scrollable content */}
            <div className="flex-1 overflow-y-auto min-h-0">
              <div className="px-5 md:px-6 py-5 space-y-5">

                {/* Rent highlight */}
                <div className="bg-blue-50 border border-blue-100 p-4 rounded-xl">
                  <p className="text-xs font-medium text-blue-600 uppercase tracking-wider mb-1">
                    Valor do Aluguel
                  </p>
                  <p className="text-2xl md:text-3xl font-bold text-blue-700">
                    R${" "}
                    {property.rent.toLocaleString("pt-BR", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                    <span className="text-sm font-normal text-blue-500 ml-1">/mês</span>
                  </p>
                </div>

                {/* Characteristics grid 2x2 */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-3">Características</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { icon: Bed, label: "Quartos", value: property.bedrooms },
                      { icon: Bath, label: "Banheiros", value: property.bathrooms },
                      { icon: Car, label: "Vagas", value: property.parkingSpaces },
                      { icon: null, label: "Área", value: `${property.area}m²`, isArea: true },
                    ].map((item) => (
                      <div
                        key={item.label}
                        className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100"
                      >
                        <div className="h-9 w-9 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                          {item.isArea ? (
                            <span className="text-blue-600 text-xs font-bold">m²</span>
                          ) : (
                            item.icon && <item.icon className="h-4 w-4 text-blue-600" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <p className="text-[11px] text-slate-500 leading-none mb-0.5">{item.label}</p>
                          <p className="text-sm font-semibold text-slate-900">{item.value}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Tenant */}
                {tenantName && (
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-50 border border-emerald-100">
                    <div className="h-9 w-9 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-emerald-600" />
                    </div>
                    <div>
                      <p className="text-[11px] text-emerald-600 leading-none mb-0.5">Inquilino Atual</p>
                      <p className="text-sm font-semibold text-slate-900">{tenantName}</p>
                    </div>
                  </div>
                )}

                {/* Description with internal scroll */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-2">Descrição</h3>
                  <div className="max-h-[120px] overflow-y-auto pr-1">
                    <p className="text-sm text-slate-500 leading-relaxed whitespace-pre-line">
                      {property.description || "Nenhuma descrição disponível."}
                    </p>
                  </div>
                </div>

                {/* Full address */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-2">Endereço Completo</h3>
                  <div className="space-y-0.5 text-sm text-slate-500">
                    <p>{property.address}</p>
                    <p>{property.neighborhood}</p>
                    <p>
                      {property.city} - {property.state}
                    </p>
                    {property.zipCode && <p>CEP: {property.zipCode}</p>}
                  </div>
                </div>
              </div>
            </div>

            {/* Footer — sticky at bottom */}
            <div className="border-t border-slate-100 bg-white px-5 md:px-6 py-3 flex gap-3 flex-shrink-0">
              <Button
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
                onClick={handleEdit}
              >
                <Edit className="h-4 w-4 mr-2" />
                Editar
              </Button>
              <Button
                variant="destructive"
                className="flex-1 shadow-sm"
                onClick={handleDelete}
              >
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