import { LoginForm } from "@/features/admin/auth/components/login-form";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/50 p-6">
      <div className="w-full max-w-sm rounded-xl border bg-background p-6 shadow-sm">
        {/* Logo */}
        <div className="mb-6 flex items-center gap-2.5 border-b pb-5">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-foreground text-xs font-bold text-background">
            DC
          </span>
          <div>
            <p className="text-sm font-semibold leading-none">Distri Choco</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Panel interno
            </p>
          </div>
        </div>

        <h1 className="mb-1 text-xl font-semibold">Bienvenido</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Ingresá tus credenciales para acceder al panel.
        </p>

        <LoginForm />
      </div>
    </div>
  );
}