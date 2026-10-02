"use client";

import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { useEffect } from "react";
import type { MapClient } from "@/features/admin/client-map/types";

export type ClientsMapProps = {
  clients: MapClient[];
  isLoading: boolean;
  isError: boolean;
  selectedBranchId: number | null;
  onSelectBranch: (branchId: number) => void;
};

const defaultIcon = L.icon({
  iconUrl: "/marker-icon.png",
  iconRetinaUrl: "/marker-icon.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

function ChangeMapCenter({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();

  useEffect(() => {
    map.setView([lat, lng], map.getZoom());
  }, [lat, lng, map]);

  return null;
}

export function ClientsMap({
  clients,
  isLoading,
  isError,
  selectedBranchId,
  onSelectBranch,
}: ClientsMapProps) {
  if (isLoading) {
    return (
      <div className="flex h-[600px] items-center justify-center rounded-xl border">
        Cargando mapa...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-[600px] items-center justify-center rounded-xl border">
        Error al cargar el mapa
      </div>
    );
  }

  if (clients.length === 0) {
    return (
      <div className="flex h-[600px] items-center justify-center rounded-xl border">
        No hay sucursales con coordenadas para mostrar
      </div>
    );
  }

  const selectedBranch =
    clients.find((client) => client.branch_id === selectedBranchId) ?? clients[0];

  return (
    <MapContainer
      center={[selectedBranch.lat, selectedBranch.lng]}
      zoom={12}
      style={{ height: "600px", width: "100%" }}
      className="rounded-xl"
    >
      <ChangeMapCenter lat={selectedBranch.lat} lng={selectedBranch.lng} />

      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {clients.map((client) => (
        <Marker
          key={client.branch_id}
          position={[client.lat, client.lng]}
          icon={defaultIcon}
          eventHandlers={{
            click: () => onSelectBranch(client.branch_id),
          }}
        >
          <Popup>
            <div className="space-y-1">
              <p className="font-semibold">{client.client_name}</p>
              <p className="text-sm">
                {client.branch_name}
                {client.branch_is_main ? " (Principal)" : ""}
              </p>
              {client.branch_address ? <p>{client.branch_address}</p> : null}
              {client.branch_city ? <p>{client.branch_city}</p> : null}
              {client.sales_rep_name ? (
                <p>Vendedor: {client.sales_rep_name}</p>
              ) : null}
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}