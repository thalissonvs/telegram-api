import { useState, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import { useRouter } from "next/router";

const ClientsPage = () => {
  const [clients, setClients] = useState([]);
  const [payments, setPayments] = useState([]);
  const [prizes, setPrizes] = useState([]);
  const [investments, setInvestments] = useState([]);

  useEffect(() => {
    try {
      require("bootstrap/dist/js/bootstrap.bundle.min");

      document.getElementById("payments_div").style.display = "none";
      document.getElementById("prizes_div").style.display = "none";
      document.getElementById("edit_client").style.display = "none";
      document.getElementById("investments_div").style.display = "none";
      document.getElementById("clients").style.display = "block";

      fetch("/api/v1/client")
        .then((response) => {
          return response.json();
        })
        .then((data) => {
          setClients(data);
        });
    } catch (error) {
      console.error("Error fetching clients:", error);
    }
  }, []);

  const handleShowPayments = (client_id) => {
    fetch(`/api/v1/payments?client_id=${client_id}`)
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        const client_payments = [];
        for (const payment of data) {
          if (payment.price > 0) {
            client_payments.push(payment);
          }
        }
        setPayments(client_payments);
        document.getElementById("payments_div").style.display = "block";
        document.getElementById("clients").style.display = "none";
      });
  };

  const handleShowAwards = (client_id) => {
    fetch(`/api/v1/prizes?client_id=${client_id}`)
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        setPrizes(data);
        document.getElementById("prizes_div").style.display = "block";
        document.getElementById("clients").style.display = "none";
        document.getElementById("payments_div").style.display = "none";
      });
  };

  const handleEdit = (data) => {
    document.getElementById("clients").style.display = "none";
    document.getElementById("edit_client").style.display = "block";
    document.getElementById("first_name").value = clients[data].first_name;
    document.getElementById("email").value = clients[data].email;
    document.getElementById("pix_type").value = clients[data].pix_type;
    document.getElementById("pix_key").value = clients[data].pix_key;
  };

  const updateClientData = (event) => {
    event.preventDefault();
    const first_name = document.getElementById("first_name").value;
    const email = document.getElementById("email").value;
    const pix_type = document.getElementById("pix_type").value;
    const pix_key = document.getElementById("pix_key").value;

    fetch("/api/v1/client", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ first_name, email, pix_type, pix_key }),
    })
      .then((response) => {
        if (response.ok) {
          alert("Dados atualizados com sucesso");
        } else {
          alert("Erro ao atualizar dados");
        }
      })
      .catch((error) => {
        alert("Error updating client data:" + error);
      });
  };

  const handleShowInvestments = (client_id) => {
    fetch(`/api/v1/payments?client_id=${client_id}`)
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        const client_investments = [];
        for (const payment of data) {
          if (payment.price < 0) {
            client_investments.push(payment);
          }
        }
        setInvestments(client_investments);
        document.getElementById("investments_div").style.display = "block";
        document.getElementById("clients").style.display = "none";
      });
  };
  const handleBack = () => {
    document.getElementById("payments_div").style.display = "none";
    document.getElementById("prizes_div").style.display = "none";
    document.getElementById("investments_div").style.display = "none";
    document.getElementById("clients").style.display = "block";
    document.getElementById("edit_client").style.display = "none";
  };

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
                <a class="nav-link" href="#">
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
      <div className="container mt-4" id="clients">
        <h2>Clientes</h2>
        <div className="table-responsive mt-3">
          <table className="table table-bordered">
            <thead>
              <tr>
                <th>ID</th>
                <th>Primeiro nome</th>
                <th>Email</th>
                <th>Tipo de chave PIX</th>
                <th>Chave PIX</th>
                <th>Saldo</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((client, index) => (
                <tr key={index}>
                  <td>{client.id}</td>
                  <td>{client.first_name}</td>
                  <td>{client.email}</td>
                  <td>{client.pix_type}</td>
                  <td>{client.pix_key}</td>
                  <td>{client.balance}</td>
                  <td className="align-middle">
                    <div className="row w-100">
                      <div className="col-12 col-sm-auto mb-2 mb-sm-0">
                        <button
                          className="btn btn-outline-primary my-1 btn-sm"
                          onClick={() => handleEdit(index)}
                        >
                          Editar
                        </button>
                      </div>
                      <div className="col-12 col-sm-auto mb-2 mb-sm-0">
                        <button
                          className="btn btn-outline-primary my-1 btn-sm"
                          onClick={() => handleShowPayments(client.id)}
                        >
                          Pagamentos
                        </button>
                      </div>
                      <div className="col-12 col-sm-auto">
                        <button
                          className="btn btn-outline-primary my-1 btn-sm"
                          onClick={() => handleShowAwards(index)}
                        >
                          Prêmios
                        </button>
                      </div>
                      <div className="col-12 col-sm-auto">
                        <button
                          className="btn btn-outline-primary my-1 btn-sm"
                          onClick={() => handleShowInvestments(index)}
                        >
                          Investimentos
                        </button>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="container mt-4" id="payments_div">
        <h2>Pagamentos do cliente</h2>
        <div className="table-responsive mt-3">
          <table className="table table-bordered">
            <thead>
              <tr>
                <th>ID do cliente</th>
                <th>Preço</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment, index) => (
                <tr key={index}>
                  <td>{payment.client_id}</td>
                  <td>{payment.price}</td>
                  <td>{payment.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            className="btn btn-outline-primary my-1 btn-sm"
            onClick={() => handleBack()}
          >
            Voltar
          </button>
        </div>
      </div>
      <div className="container mt-4" id="prizes_div">
        <h2>Prêmios do cliente</h2>
        <div className="table-responsive mt-3">
          <table className="table table-bordered">
            <thead>
              <tr>
                <th>ID do cliente</th>
                <th>Prêmio</th>
                <th>Data</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {prizes.map((prize, index) => (
                <tr key={index}>
                  <td>{prize.client_id}</td>
                  <td>{prize.price}</td>
                  <td>{prize.date}</td>
                  <td>{prize.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            className="btn btn-outline-primary my-1 btn-sm"
            onClick={() => handleBack()}
          >
            Voltar
          </button>
        </div>
      </div>
      <div className="container mt-4" id="investments_div">
        <h2>Investimentos do cliente</h2>
        <div className="table-responsive mt-3">
          <table className="table table-bordered">
            <thead>
              <tr>
                <th>ID do cliente</th>
                <th>Valor</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {prizes.map((investment, index) => (
                <tr key={index}>
                  <td>{investment.client_id}</td>
                  <td>{investment.price}</td>
                  <td>{investment.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            className="btn btn-outline-primary my-1 btn-sm"
            onClick={() => handleBack()}
          >
            Voltar
          </button>
        </div>
      </div>
      <div className="container mt-4" id="edit_client">
        <h2>Editar dados do cliente</h2>
        <form onSubmit={updateClientData}>
          <div className="mb-3">
            <label for="first_name">Primeiro nome</label>
            <input
              type="text"
              className="form-control"
              id="first_name"
              placeholder="Primeiro nome"
            />
          </div>
          <div className="mb-3">
            <label for="email" className="form-label">
              Email
            </label>
            <input
              type="email"
              className="form-control"
              id="email"
              placeholder="Email"
            />
          </div>
          <div className="mb-3">
            <label for="pix_type" className="form-label">
              Tipo de chave PIX
            </label>
            <input
              type="text"
              className="form-control"
              id="pix_type"
              placeholder="Tipo de chave PIX"
            />
          </div>
          <div className="mb-3">
            <label for="pix_key" className="form-label">
              Chave PIX
            </label>
            <input
              type="text"
              className="form-control"
              id="pix_key"
              placeholder="Chave PIX"
            />
          </div>
          <button type="submit" className="btn btn-primary mb-2 w-100">
            Salvar
          </button>
        </form>
        <button className="btn btn-danger w-100" onClick={handleBack}>
          Voltar
        </button>
      </div>
    </>
  );
};

export default ClientsPage;
