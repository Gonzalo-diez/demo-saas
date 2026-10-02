import {
  LayoutDashboard,
  Package,
  ArrowLeftRight,
  Users,
  MapPin,
  FileText,
  Truck,
  ShoppingCart,
  ClipboardList,
  UserCheck,
  Map,
  BarChart2,
  Wallet,
  Landmark,
  type LucideIcon,
} from "lucide-react";

export type NavigationItem = {
  href: string;
  label: string;
  shortLabel?: string;
  icon: LucideIcon;
};

export const NAV_ITEMS: NavigationItem[] = [
  {
    href: "/admin/dashboard",
    label: "Dashboard",
    shortLabel: "Dash",
    icon: LayoutDashboard,
  },
  {
    href: "/admin/products",
    label: "Productos",
    shortLabel: "Prod",
    icon: Package,
  },
  {
    href: "/admin/inventory-movements",
    label: "Movimientos de inventario",
    shortLabel: "Stock",
    icon: ArrowLeftRight,
  },
  { href: "/admin/clients", label: "Clientes", shortLabel: "Cli", icon: Users },
  {
    href: "/admin/client-map",
    label: "Mapa clientes",
    shortLabel: "Mapa Clientes",
    icon: MapPin,
  },
  {
    href: "/admin/sales",
    label: "Ventas",
    shortLabel: "Vtas",
    icon: FileText,
  },
  {
    href: "/admin/suppliers",
    label: "Proveedores",
    shortLabel: "Prov",
    icon: Truck,
  },
  {
    href: "/admin/purchases",
    label: "Compras",
    shortLabel: "Comp",
    icon: ShoppingCart,
  },
  {
    href: "/admin/checks",
    label: "Cheques",
    shortLabel: "Cheq",
    icon: Landmark,
  },
  {
    href: "/admin/account-movements",
    label: "Cuenta corriente",
    shortLabel: "Cta Cte",
    icon: Wallet,
  },
  {
    href: "/admin/orders",
    label: "Pedidos",
    shortLabel: "Ped",
    icon: ClipboardList,
  },
  {
    href: "/admin/sales-reps",
    label: "Vendedores",
    shortLabel: "Vend",
    icon: UserCheck,
  },
  {
    href: "/admin/sales-rep-map",
    label: "Mapa vendedores",
    shortLabel: "Mapa Vendedores",
    icon: Map,
  },
  {
    href: "/admin/analytics",
    label: "Analiticas",
    shortLabel: "Analitica",
    icon: BarChart2,
  },
];

export const PAGE_TITLES: Record<string, string> = {
  "/admin/dashboard": "Dashboard",
  "/admin/products": "Productos",
  "/admin/inventory-movements": "Movimientos de inventario",
  "/admin/clients": "Clientes",
  "/admin/suppliers": "Proveedores",
  "/admin/purchases": "Compras",
  "/admin/checks": "Cheques",
  "/admin/account-movements": "Cuenta corriente",
  "/admin/sales": "Ventas",
  "/admin/orders": "Pedidos",
  "/admin/sales-reps": "Vendedores",
  "/admin/client-map": "Mapa clientes",
  "/admin/sales-rep-map": "Mapa vendedores",
  "/admin/analytics": "Analiticas",
};