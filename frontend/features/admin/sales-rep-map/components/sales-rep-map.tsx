"use client";

import L from "leaflet";
import {
  Circle,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";
import { Fragment, useEffect } from "react";
import type { MapSalesRep } from "@/features/admin/sales-rep-map/types";

export type SalesRepMapProps = {
  salesReps: MapSalesRep[];
  centerLat?: number;
  centerLng?: number;
  radiusKm?: number;
  isLoading: boolean;
  isError: boolean;
  selectedId: number | null;
  onSelect: (id: number) => void;
};

// Centro de fallback (Buenos Aires) solo para cuando no hay ningún
// vendedor con coordenadas ni filtro de zona activo.
const FALLBACK_CENTER: [number, number] = [-34.6037, -58.3816];
const FALLBACK_ZOOM = 4;

const defaultIcon = L.icon({
  iconUrl: "/marker-icon.png",
  iconRetinaUrl: "/marker-icon.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const searchCenterIcon = L.divIcon({
  className: "",
  html:
    '<div style="width:16px;height:16px;border-radius:9999px;' +
    'background:#2563eb;border:2px solid white;' +
    'box-shadow:0 0 0 3px rgba(37,99,235,0.35);"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

function FocusPoint({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();

  useEffect(() => {
    map.setView([lat, lng], Math.max(map.getZoom(), 10));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lng]);

  return null;
}

function FitAllReps({ repsWithCoords }: { repsWithCoords: MapSalesRep[] }) {
  const map = useMap();

  useEffect(() => {
    if (repsWithCoords.length === 0) return;

    if (repsWithCoords.length === 1) {
      map.setView(
        [repsWithCoords[0].home_lat!, repsWithCoords[0].home_lng!],
        11
      );
      return;
    }

    const bounds = L.latLngBounds(
      repsWithCoords.map(
        (r) => [r.home_lat!, r.home_lng!] as [number, number]
      )
    );

    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repsWithCoords]);

  return null;
}

export function SalesRepMap({
  salesReps,
  centerLat,
  centerLng,
  radiusKm,
  isLoading,
  isError,
  selectedId,
  onSelect,
}: SalesRepMapProps) {
  if (isLoading) {
    return (
      <div className="flex h-[600px] items-center justify-center rounded-xl border text-sm text-muted-foreground">
        Cargando mapa...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-[600px] items-center justify-center rounded-xl border text-sm text-destructive">
        Error al cargar el mapa
      </div>
    );
  }

  const repsWithCoords = salesReps.filter(
    (r) => r.home_lat != null && r.home_lng != null
  );

  const hasGeoFilter = centerLat !== undefined && centerLng !== undefined;

  if (repsWithCoords.length === 0 && !hasGeoFilter) {
    return (
      <div className="flex h-[600px] items-center justify-center rounded-xl border text-sm text-muted-foreground">
        No hay vendedores con coordenadas cargadas
      </div>
    );
  }

  const selectedRep = repsWithCoords.find((r) => r.id === selectedId);

  const initialCenter: [number, number] = hasGeoFilter
    ? [centerLat!, centerLng!]
    : repsWithCoords[0]
    ? [repsWithCoords[0].home_lat!, repsWithCoords[0].home_lng!]
    : FALLBACK_CENTER;

  return (
    <MapContainer
      center={initialCenter}
      zoom={hasGeoFilter ? 10 : FALLBACK_ZOOM}
      style={{ height: "600px", width: "100%" }}
      className="rounded-xl"
    >
      {/* Prioridad de foco: vendedor seleccionado > filtro de zona > todos */}
      {selectedRep ? (
        <FocusPoint lat={selectedRep.home_lat!} lng={selectedRep.home_lng!} />
      ) : hasGeoFilter ? (
        <FocusPoint lat={centerLat!} lng={centerLng!} />
      ) : (
        <FitAllReps repsWithCoords={repsWithCoords} />
      )}

      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {hasGeoFilter && (
        <Fragment>
          <Marker position={[centerLat!, centerLng!]} icon={searchCenterIcon}>
            <Popup>Centro de búsqueda</Popup>
          </Marker>

          {radiusKm != null && radiusKm > 0 && (
            <Circle
              center={[centerLat!, centerLng!]}
              radius={radiusKm * 1000}
              pathOptions={{
                color: "#2563eb",
                fillColor: "#2563eb",
                fillOpacity: 0.04,
                weight: 1.5,
                dashArray: "6 6",
              }}
            />
          )}
        </Fragment>
      )}

      {repsWithCoords.map((rep) => (
        <Marker
          key={rep.id}
          position={[rep.home_lat!, rep.home_lng!]}
          icon={defaultIcon}
          eventHandlers={{
            click: () => onSelect(rep.id),
          }}
        >
          <Popup>
            <div className="space-y-1">
              <p className="font-semibold">{rep.name}</p>
              {rep.coverage_radius_km != null && (
                <p className="text-sm">
                  Cobertura: {rep.coverage_radius_km} km
                </p>
              )}
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Coverage radius circles */}
      {repsWithCoords
        .filter((r) => r.coverage_radius_km != null && r.coverage_radius_km > 0)
        .map((rep) => (
          <Circle
            key={`circle-${rep.id}`}
            center={[rep.home_lat!, rep.home_lng!]}
            radius={rep.coverage_radius_km! * 1000}
            pathOptions={{
              color: rep.id === selectedId ? "#2563eb" : "#64748b",
              fillColor: rep.id === selectedId ? "#2563eb" : "#64748b",
              fillOpacity: 0.08,
              weight: rep.id === selectedId ? 2 : 1,
            }}
          />
        ))}
    </MapContainer>
  );
}
