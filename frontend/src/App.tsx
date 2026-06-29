// Mapa de rotas da aplicação.
//
// /login é pública. Tudo o resto fica dentro de <ProtectedRoute> (exige sessão)
// e usa o <Layout> com a barra de navegação.

import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Alertas from "./pages/Alertas";
import Equipamentos from "./pages/Equipamentos";
import Login from "./pages/Login";
import Viaturas from "./pages/Viaturas";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Alertas />} />
          <Route path="/viaturas" element={<Viaturas />} />
          <Route path="/equipamentos" element={<Equipamentos />} />
        </Route>
      </Route>

      {/* Qualquer rota desconhecida volta ao início. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
