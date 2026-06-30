// Mapa de rotas da aplicação.
//
// /login é pública. Tudo o resto fica dentro de <ProtectedRoute> (exige sessão)
// e usa o <Layout> com a barra de navegação. Cada entidade principal tem a sua
// listagem e (quando faz sentido) uma página de detalhe com as sub-entidades.

import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Alertas from "./pages/Alertas";
import Clientes from "./pages/Clientes";
import Equipamentos from "./pages/Equipamentos";
import EquipamentoDetalhe from "./pages/EquipamentoDetalhe";
import Funcionarios from "./pages/Funcionarios";
import FuncionarioDetalhe from "./pages/FuncionarioDetalhe";
import Login from "./pages/Login";
import Obras from "./pages/Obras";
import ObraDetalhe from "./pages/ObraDetalhe";
import Viaturas from "./pages/Viaturas";
import ViaturaDetalhe from "./pages/ViaturaDetalhe";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Alertas />} />

          <Route path="/viaturas" element={<Viaturas />} />
          <Route path="/viaturas/:id" element={<ViaturaDetalhe />} />

          <Route path="/equipamentos" element={<Equipamentos />} />
          <Route path="/equipamentos/:id" element={<EquipamentoDetalhe />} />

          <Route path="/funcionarios" element={<Funcionarios />} />
          <Route path="/funcionarios/:id" element={<FuncionarioDetalhe />} />

          <Route path="/clientes" element={<Clientes />} />

          <Route path="/obras" element={<Obras />} />
          <Route path="/obras/:id" element={<ObraDetalhe />} />
        </Route>
      </Route>

      {/* Qualquer rota desconhecida volta ao início. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
