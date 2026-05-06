"use client";

import dynamic from "next/dynamic";

const SignUp = dynamic(
  () => import("@clerk/nextjs").then((mod) => ({ default: mod.SignUp })),
  { ssr: false },
);

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="flex w-full max-w-md flex-col items-center gap-8 px-4">
        <div className="flex flex-col items-center gap-2 text-center">
          <span className="text-2xl font-bold tracking-tight">Convo</span>
          <p className="text-sm text-muted-foreground">
            Configure seu agente SDR em menos de 20 minutos
          </p>
        </div>
        <SignUp
          appearance={{
            elements: {
              rootBox: "w-full",
              card: "shadow-none border border-border rounded-xl w-full",
              headerTitle: "text-foreground font-semibold",
              headerSubtitle: "text-muted-foreground",
              formButtonPrimary:
                "bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg",
              footerActionLink: "text-foreground font-medium hover:underline",
            },
          }}
        />
      </div>
    </div>
  );
}
