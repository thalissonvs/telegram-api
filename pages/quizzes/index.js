import { useState, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";

const QuizzesPage = () => {
  const [quizzes, setQuizzes] = useState([]);

  useEffect(() => {
    try {
      require("bootstrap/dist/js/bootstrap.bundle.min");
      fetch("/api/v1/quizzes")
        .then((response) => {
          return response.json();
        })
        .then((data) => {
          setQuizzes(data);
        });
    } catch (error) {
      console.error("Error fetching quizzes:", error);
    }
  }, []);

  const handleDelete = (index) => {
    const question = quizzes[index].question;
    fetch("/api/v1/quizzes", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    })
      .then((response) => {
        if (response.ok) {
          const updatedQuizzes = quizzes.filter((quiz, i) => i !== index);
          setQuizzes(updatedQuizzes);
          alert("Quiz excluído com sucesso");
        } else {
          alert("Erro ao excluir quiz");
        }
      })
      .catch((error) => {
        console.error("Error deleting quiz:", error);
      });
  };

  const handleAddQuiz = (e) => {
    e.preventDefault();
    const newQuiz = {
      question: document.getElementById("question").value,
      optionA: document.getElementById("optionA").value,
      optionB: document.getElementById("optionB").value,
      optionC: document.getElementById("optionC").value,
      optionD: document.getElementById("optionD").value,
      correctOption: document.getElementById("correctAnswer").value,
      difficulty: document.getElementById("difficulty").value,
    };
    const updatedQuizzes = [...quizzes, newQuiz];
    setQuizzes(updatedQuizzes);
    sessionStorage.setItem("quizzes", JSON.stringify(updatedQuizzes));

    const form = document.getElementById("newquiz");
    form.style.display = "none";
    const button = document.getElementById("addNewQuiz");
    button.style.visibility = "visible";

    // faz requisição para adicionar ao banco de dados
    fetch("/api/v1/quizzes", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(newQuiz),
    })
      .then((response) => {
        if (response.ok) {
          alert("Quiz adicionado com sucesso");
        } else {
          alert("Erro ao adicionar quiz");
        }
      })
      .catch((error) => {
        console.error("Error adding quiz:", error);
      });
  };

  const showAddNewQuiz = () => {
    const newQuiz = document.getElementById("newquiz");
    newQuiz.style.display = "block";
    const button = document.getElementById("addNewQuiz");
    button.style.visibility = "hidden";
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
                <a class="nav-link" href="/prizes">
                  Prêmios
                </a>
              </li>
            </ul>
          </div>
        </div>
      </nav>
      <div className="container mt-5">
        <h2>Quizzes</h2>
        <div className="table-responsive mt-3">
          <table className="table table-bordered">
            <thead>
              <tr>
                <th>Pergunta</th>
                <th>Opção A</th>
                <th>Opção B</th>
                <th>Opção C</th>
                <th>Opção D</th>
                <th>Dificuldade</th>
                <th>Resposta Correta</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {quizzes.map((quiz, index) => (
                <tr key={index}>
                  <td>{quiz.question}</td>
                  <td>{quiz.optionA}</td>
                  <td>{quiz.optionB}</td>
                  <td>{quiz.optionC}</td>
                  <td>{quiz.optionD}</td>
                  <td>{quiz.difficulty}</td>
                  <td>{quiz.correctOption}</td>
                  <td>
                    <button
                      className="btn btn-danger"
                      onClick={() => handleDelete(index)}
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <form style={{ display: "none" }} id="newquiz" onSubmit={handleAddQuiz}>
          <h2>Novo Quiz</h2>
          <div className="mb-3">
            <label htmlFor="question" className="form-label">
              Pergunta:
            </label>
            <input type="text" className="form-control" id="question" />
          </div>
          <div className="row mb-3">
            <div className="col-md-6 col-sm-12">
              <label htmlFor="optionA" className="form-label">
                Opção A:
              </label>
              <input type="text" className="form-control" id="optionA" />
            </div>
            <div className="col-md-6 col-sm-12">
              <label htmlFor="optionB" className="form-label">
                Opção B:
              </label>
              <input type="text" className="form-control" id="optionB" />
            </div>
          </div>
          <div className="row mb-3">
            <div className="col-md-6 col-sm-12">
              <label htmlFor="optionC" className="form-label">
                Opção C:
              </label>
              <input type="text" className="form-control" id="optionC" />
            </div>
            <div className="col-md-6 col-sm-12">
              <label htmlFor="optionD" className="form-label">
                Opção D:
              </label>
              <input type="text" className="form-control" id="optionD" />
            </div>
          </div>
          <div className="row mb-3">
            <div className="col-md-6 col-sm-12">
              <label htmlFor="difficulty" className="form-label">
                Dificuldade:
              </label>
              <select className="form-select" id="difficulty">
                <option value="1">1 (Fácil)</option>
                <option value="2">2 (Normal)</option>
                <option value="3">3 (Difícil)</option>
              </select>
            </div>
            <div className="col-md-6 col-sm-12">
              <label htmlFor="correctAnswer" className="form-label">
                Resposta Correta:
              </label>
              <select className="form-select" id="correctAnswer">
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
              </select>
            </div>
          </div>

          <div className="col-auto text-center">
            <button type="submit" className="btn btn-primary mt-3 w-100">
              Enviar
            </button>
          </div>
        </form>
        <button
          id="addNewQuiz"
          className="btn btn-primary mt-3"
          style={{ visibility: "visible" }}
          onClick={showAddNewQuiz}
        >
          Adicionar Novo Quiz
        </button>
      </div>
    </>
  );
};

export default QuizzesPage;
