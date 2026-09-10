"use client";

import type { ReactNode } from "react";
import { AuthProvider } from "react-oidc-context";

type Props = {
    children: ReactNode;
};

export default function CognitoAuthProvider({ children }: Props) {
    const config = {
    authority: process.env.NEXT_PUBLIC_COGNITO_AUTHORITY!,
    client_id: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
    redirect_uri: process.env.NEXT_PUBLIC_COGNITO_REDIRECT_URI!,
    response_type: "code",
    scope: "openid email profile",

    onSigninCallback: () => {
        window.history.replaceState(
        {},
        document.title,
        window.location.pathname
    );
    },
  };

  return (
    <AuthProvider {...config}>
      {children}
    </AuthProvider>
  );
}