
let acces_token = '';
let tasks = {};
function Login() {
  const username = document.getElementsByName('username')[0].value;
  const password = document.getElementsByName('password')[0].value;

  let headers = new Headers();

  headers.append('Content-Type', 'application/json');
  headers.append('Accept', 'application/json');

  headers.append('Access-Control-Allow-Origin', 'http://127.0.0.1:5000');

  fetch('http://127.0.0.1:5000/user/login', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ "username": username, "password": password })
  })
    .then(response => response.json())
    .then(data => {
      console.log('Ответ сервера:', data);
      console.log(data['code']);
      acces_token = data['Authorization'];
      console.log(data['user']);
      console.log(data['role']);
      if (data['code'] == 200) {

        document.querySelector("body > header > div > span.role").textContent = data['role'];
        document.querySelector("body > header > div > span.username").textContent = data['user'];
        load_tasks();
      } else {
        alert('Неправильный логин или пароль.');
      }
    })
    .catch(error => {

      alert('Ошибка: сервер не отвечает');
      console.error('Ошибка:', error);
    });

}

function Logout() {

  let headers = new Headers();

  headers.append('Content-Type', 'application/json');
  headers.append('Accept', 'application/json');

  headers.append('Access-Control-Allow-Origin', 'http://127.0.0.1:5000');
  headers.append('Authorization', 'Bearer ' + acces_token);

  fetch('http://127.0.0.1:5000/user/logout', {
    method: 'POST',
    headers: headers,

  })
    .then(response => response.json())
    .then(data => {

      console.log('Ответ сервера:', data);

      if (data['code'] == 200) {

        document.querySelector("body > header > div > span.role").textContent = "";
        document.querySelector("body > header > div > span.username").textContent = "";

        var sel_log = document.querySelector('.Login');
        sel_log.style.display = 'block';

        var sel_tasks = document.querySelector('.task_list');
        sel_tasks.style.display = 'none';
        acces_token = "";
        tasks = {};
        data = {};

      } else {
        alert('ошибка.');
      }
    })
    .catch(error => {
      alert('Ошибка: сервер не отвечает');
      console.error('Ошибка:', error);
    });

}

function Drag_task(targetSection, task_id) {


  let headers = new Headers();
  headers.append('Content-Type', 'application/json');
  headers.append('Accept', 'application/json');

  headers.append('Access-Control-Allow-Origin', 'http://127.0.0.1:5000');
  headers.append('Authorization', 'Bearer ' + acces_token);

  const targetSection2 = targetSection.replace(/ /g, '_');
  console.log(targetSection2);
  console.log(task_id);

  fetch('http://127.0.0.1:5000/task/status', {
    method: 'PUT',
    headers: headers,
    body: JSON.stringify({ "task_id": task_id, "new_status": targetSection2 })
  })
    .then(response => {
      console.log('Код ответа сервера:', response.status);
      return response.json();
    })
    .then(data => {
      console.log('Ответ сервера:', data);
      if (data['code'] == 200) {
      } else {
        alert('Ошибка: ' + data['Message']);
        load_tasks();
      }
    })
    .catch(error => {
      console.error('Ошибка: ' + data['Message'], error);
    });

}
function load_tasks() {
  let headers = new Headers();

  headers.append('Content-Type', 'application/json');
  headers.append('Accept', 'application/json');
  headers.append('Authorization', 'Bearer ' + acces_token)
  headers.append('Access-Control-Allow-Origin', 'http://127.0.0.1:5000');

  fetch('http://127.0.0.1:5000/task/', {
    method: 'GET',
    headers: headers,

  })
    .then(response => {
      console.log('Код ответа сервера:', response.status);
      return response.json();
    })
    .then(data => {
      console.log('Ответ сервера:', data);
      console.log(data['code']);

      if (data['code'] == 200) {
        tasks = data;
        create_tasklist(tasks);
      } else {
        alert('Неверный токен.');
      }
    })
    .catch(error => {
      alert('Ошибка: сервер не отвечает');
      console.error('Ошибка:', error);
    });

}
function load_tasks_by_text() {
  let headers = new Headers();

  headers.append('Content-Type', 'application/json');
  headers.append('Accept', 'application/json');
  headers.append('Authorization', 'Bearer ' + acces_token)
  headers.append('Access-Control-Allow-Origin', 'http://127.0.0.1:5000');

  var search_text = document.querySelector("body > header > div:nth-child(2) > input").value;
  console.log(search_text);

  fetch('http://127.0.0.1:5000/task/?text=' + search_text, {
    method: 'GET',

    headers: headers,
  })
    .then(response => response.json())
    .then(data => {
      console.log('Ответ сервера:', data);
      console.log(data['code']);

      if (data['code'] == 200) {
        tasks = data;
        create_tasklist(tasks);
      } else {
        alert('Неверный токен.');
      }
    })
    .catch(error => {
      alert('Ошибка: сервер не отвечает');
      console.error('Ошибка:', error);
    });

}
function create_tasklist(tasks) {

  const elements = document.querySelectorAll('.task');

  for (let i = 0; i < elements.length; i++) {
    elements[i].remove();
  }
  var sel_log = document.querySelector('.Login');
  sel_log.style.display = 'none';

  var sel_tasks = document.querySelector('.task_list');
  sel_tasks.style.display = 'block';

  var new_status = document.querySelector("body > div.task_list > div:nth-child(1) > div");
  if (tasks.hasOwnProperty("To_do")) {
    for (let item of tasks['To_do']) {
      console.log(item);
      add_task(new_status, item);
    }
  }
  if (tasks.hasOwnProperty("In_progress")) {
    var new_status = document.querySelector("body > div.task_list > div:nth-child(2) > div");
    for (let item of tasks['In_progress']) {
      console.log(item);
      add_task(new_status, item);
    }
  }
  if (tasks.hasOwnProperty("Code_review")) {
    var new_status = document.querySelector("body > div.task_list > div:nth-child(3) > div");
    for (let item of tasks['Code_review']) {
      console.log(item);
      add_task(new_status, item);
    }
  }
  if (tasks.hasOwnProperty("Dev_test")) {
    var new_status = document.querySelector("body > div.task_list > div:nth-child(4) > div");
    for (let item of tasks['Dev_test']) {
      console.log(item);
      add_task(new_status, item);
    }
  }
  if (tasks.hasOwnProperty("Testing")) {
    var new_status = document.querySelector("body > div.task_list > div:nth-child(5) > div");
    for (let item of tasks['Testing']) {
      console.log(item);
      add_task(new_status, item);
    }
  }
  if (tasks.hasOwnProperty("Done")) {
    var new_status = document.querySelector("body > div.task_list > div:nth-child(6) > div");
    for (let item of tasks['Done']) {
      console.log(item);
      add_task(new_status, item);
    }
  }
  if (tasks.hasOwnProperty("Wont_fix")) {
    var new_status = document.querySelector("body > div.task_list > div:nth-child(7) > div");
    for (let item of tasks['Wont_fix']) {
      console.log(item);
      add_task(new_status, item);
    }
  }

}

function add_task(targetElement, new_task) {
  const newElement = document.createElement("div");
  newElement.setAttribute("class", "task");
  newElement.setAttribute("id", new_task['id']);
  newElement.setAttribute("draggable", "true");
  newElement.setAttribute("ondragstart", "drag(event)");

  const editButton = document.createElement("button");
  editButton.setAttribute("class", "task-edit-button");
  editButton.textContent = "EDIT";

  const taskTitle = document.createElement("h3");
  taskTitle.setAttribute("class", "task-title");
  taskTitle.textContent = new_task["title"];

  const taskDescription = document.createElement("p");
  taskDescription.setAttribute("class", "task-description");
  taskDescription.textContent = new_task["description"];

  const priority = document.createElement("p");
  priority.textContent = "Priority: " + new_task["priority"];

  const executor = document.createElement("p");

  if (new_task.hasOwnProperty("executor")) {
    console.log(new_task['executor'])
    if (new_task["executor"] != null) {
      executor.innerHTML = "Executor: " + new_task["executor"][1] + " " + new_task["executor"][2];
    }
  }
  else {
    executor.innerHTML = "Executor: " + "-";
  }

  const owner = document.createElement("p");
  owner.textContent = "Creator: " + new_task["creator"][1];

  const lastModified = document.createElement("p");
  lastModified.textContent = "Last modified: " + new_task["edit_date"];

  newElement.appendChild(editButton);
  newElement.appendChild(taskTitle);
  newElement.appendChild(taskDescription);
  newElement.appendChild(priority);
  newElement.appendChild(executor);
  newElement.appendChild(owner);
  newElement.appendChild(lastModified);

  targetElement.appendChild(newElement);
}
