import database from "../../../infra/database";

async function quizzes(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET, POST, PUT, DELETE, OPTIONS",
  );
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  const methodsMap = {
    DELETE: deleteQuiz,
    GET: getQuizzes,
    POST: postQuizzes,
  };

  if (methodsMap[req.method]) {
    return methodsMap[req.method](req, res);
  } else {
    res.status(405).end();
  }
}

async function getQuizzes(req, res) {
  const difficulty = req.query.difficulty;

  const getQuizzesQuery = `
    SELECT q.id, q.question, q.difficulty, o.option_label, o.option_text, o.is_correct
    FROM quizzes q
    JOIN options o ON q.id = o.quiz_id
    ${difficulty ? `WHERE q.difficulty = ${difficulty}` : ""}
  `;
  const result = await database.query(getQuizzesQuery);
  const quizzes = result.rows;
  // formata o resultado para o formato esperado
  const formattedQuizzes = formatQuizzes(quizzes);
  res.status(200).json(formattedQuizzes);
}

async function postQuizzes(req, res) {
  const question = req.body.question;
  // verifica se a pergunta já existe
  const questionExistsResponse = await database.query(`
    SELECT question
    FROM quizzes
    WHERE question = '${question}';
  `);
  const questionExists = questionExistsResponse.rowCount > 0;

  if (questionExists) {
    res.status(400).json({ error: "Question already exists" });
    return;
  }

  const postQuizzesQuery = `
    INSERT INTO quizzes (question, difficulty)
    VALUES ('${req.body.question}', ${req.body.difficulty})
    RETURNING id;
  `;
  console.log(postQuizzesQuery);
  const result = await database.query(postQuizzesQuery);
  const quizId = result.rows[0].id;

  const postOptionsQuery = `
    INSERT INTO options (quiz_id, option_label, option_text, is_correct)
    VALUES
      (${quizId}, 'A', '${req.body.optionA}', ${req.body.correctOption === "A"}),
      (${quizId}, 'B', '${req.body.optionB}', ${req.body.correctOption === "B"}),
      (${quizId}, 'C', '${req.body.optionC}', ${req.body.correctOption === "C"}),
      (${quizId}, 'D', '${req.body.optionD}', ${req.body.correctOption === "D"});
  `;
  const status = await database.query(postOptionsQuery);
  console.log(status);
  res.status(201).json({ status: "ok" });
}

async function deleteQuiz(req, res) {
  const question = req.body.question;
  const questionIdResponse = await database.query(`
    SELECT id
    FROM quizzes
    WHERE question = '${question}';
  `);
  const questionId = questionIdResponse.rows[0].id;

  const deleteOptionsQuery = `
    DELETE FROM options
    WHERE quiz_id = ${questionId};
  `;
  const deleteQuizQuery = `
    DELETE FROM quizzes
    WHERE question = '${question}';
  `;
  await database.query(deleteOptionsQuery);
  await database.query(deleteQuizQuery);
  res.status(200).json({ status: "ok" });
}

function formatQuizzes(quizzes) {
  const formattedQuizzes = quizzes.reduce((result, quiz) => {
    const quizQuestion = result.find((q) => q.question === quiz.question);

    if (quizQuestion) {
      quizQuestion[`option${quiz.option_label}`] = quiz.option_text;
      if (quiz.is_correct) {
        quizQuestion.correctOption = quiz.option_label;
      }
    } else {
      result.push({
        id: quiz.id,
        question: quiz.question,
        [`option${quiz.option_label}`]: quiz.option_text,
        correctOption: quiz.is_correct ? quiz.option_label : null,
        difficulty: quiz.difficulty,
      });
    }

    return result;
  }, []);

  return formattedQuizzes;
}

export default quizzes;
