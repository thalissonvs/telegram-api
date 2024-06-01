import { useState, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";

const PrizesPage = () => {
  const [prizes, setPrizes] = useState([]);

  useEffect(() => {
    try {
      require("bootstrap/dist/js/bootstrap.bundle.min");
      fetch("/api/v1/prizes")
        .then((response) => {
          return response.json();
        })
        .then((data) => {
          console.log(data);
          setPrizes(data);
        });
    } catch (error) {
      console.error("Error fetching prizes:", error);
    }
  }, []);

  async function notifyPayment(prize) {
    const body = {
      price: prize.price,
      chat_id: prize.chat_id,
      id: prize.id,
    };
    try {
      await fetch("/api/v1/notifyPayment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      const updatedPrizes = prizes.map((p) => {
        if (p.id === prize.id) {
          p.status = 1;
        }
        return p;
      });
      setPrizes(updatedPrizes);
    } catch (error) {
      console.error("Error notifying payment:", error);
    }
  }

  return (
    <>
      <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
          <a class="navbar-brand" href="#">
            Painel
          </a>
          <button
            class="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarTogglerDemo03"
            aria-controls="navbarTogglerDemo03"
            aria-expanded="false"
            aria-label="Toggle navigation"
          >
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="navbarTogglerDemo03">
            <ul class="navbar-nav mr-auto mt-2 mt-lg-0">
              <li class="nav-item active">
                <a class="nav-link" href="/quizzes">
                  Quizzes
                </a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="/clients">
                  Clientes
                </a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="#">
                  Recebimentos
                </a>
              </li>
              <li class="nav-item">
                <a class="nav-link" href="#">
                  Prêmios
                </a>
              </li>
            </ul>
          </div>
        </div>
      </nav>
      <div className="container mt-5">
        <h2>Prêmios</h2>
        <div className="table-responsive mt-3">
          <table className="table table-bordered">
            <thead>
              <tr>
                <th>ID</th>
                <th>Cliente</th>
                <th>Tipo de chave</th>
                <th>Chave PIX</th>
                <th>Valor</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {prizes.map((prize, index) => (
                <tr key={prize.chat_id}>
                  <td>{prize.id}</td>
                  <td>{prize.first_name}</td>
                  <td>{prize.pix_type}</td>
                  <td>{prize.pix_key}</td>
                  <td>{prize.price}</td>
                  <td>{prize.status}</td>
                  <td>
                    {prize.status === 0 ? (
                      <button
                        className="btn btn-primary"
                        onClick={() => notifyPayment(prize)}
                      >
                        Notificar pagamento
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
};

export default PrizesPage;
