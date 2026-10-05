import { LoginForm } from "@/features/admin/auth/components/login-form";
import { TenantBrand } from "@/features/tenant/components/tenant-brand";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-sm rounded-3xl bg-card p-7 ring-[1.5px] ring-border">
        <div className="mb-6 border-b pb-5">
          <TenantBrand />
          <p className="mt-1.5 text-xs text-muted-foreground">Panel interno</p>
        </div>

        <h1 className="mb-1 text-2xl font-bold">Bienvenido</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Ingresá tus credenciales para acceder al panel.
        </p>

        <LoginForm />
      </div>
    </div>
  );
}
