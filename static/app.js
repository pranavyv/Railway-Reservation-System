/* Client-side helpers for the RRS pages.
 * The server (Python) is always the final validator; this only gives faster feedback.
 * Forms opt in with data-form="register" | "login" | "search".
 */
(function () {
  "use strict";

  var EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
  var MIN_PASSWORD = 8;

  function todayLocal() {
    var d = new Date();
    var month = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + "-" + month + "-" + day;
  }

  function clearError(input) {
    input.removeAttribute("aria-invalid");
    input.removeAttribute("aria-describedby");
    var existing = document.getElementById(input.id + "-error");
    if (existing) existing.remove();
  }

  function showError(input, message) {
    clearError(input);
    var p = document.createElement("p");
    p.className = "field-error";
    p.id = input.id + "-error";
    p.textContent = message;
    input.setAttribute("aria-invalid", "true");
    input.setAttribute("aria-describedby", p.id);
    input.insertAdjacentElement("afterend", p);
  }

  function value(form, name) {
    return form.elements[name].value.trim();
  }

  /* Each validator returns a list of [fieldName, message] pairs. */
  var validators = {
    register: function (form) {
      var errors = [];
      if (!value(form, "name")) errors.push(["name", "Enter your name."]);
      if (!EMAIL_RE.test(value(form, "email"))) errors.push(["email", "Enter a valid email address."]);
      if (form.elements.password.value.length < MIN_PASSWORD) {
        errors.push(["password", "Password must be at least " + MIN_PASSWORD + " characters."]);
      }
      return errors;
    },
    login: function (form) {
      var errors = [];
      if (!EMAIL_RE.test(value(form, "email"))) errors.push(["email", "Enter a valid email address."]);
      if (!form.elements.password.value) errors.push(["password", "Enter your password."]);
      return errors;
    },
    search: function (form) {
      var errors = [];
      var source = value(form, "source");
      var destination = value(form, "destination");
      var date = value(form, "date");
      if (!source) errors.push(["source", "Enter a source station."]);
      if (!destination) errors.push(["destination", "Enter a destination station."]);
      if (source && destination && source.toLowerCase() === destination.toLowerCase()) {
        errors.push(["destination", "Source and destination must be different."]);
      }
      if (!date) errors.push(["date", "Choose a travel date."]);
      else if (date < todayLocal()) errors.push(["date", "Travel date cannot be in the past."]);
      return errors;
    }
  };

  function attachValidation(form) {
    var validate = validators[form.dataset.form];
    if (!validate) return;

    form.addEventListener("submit", function (event) {
      Array.prototype.forEach.call(form.elements, function (el) {
        if (el.id) clearError(el);
      });
      var errors = validate(form);
      if (errors.length) {
        event.preventDefault();
        errors.forEach(function (pair) {
          showError(form.elements[pair[0]], pair[1]);
        });
        form.elements[errors[0][0]].focus();
      }
    });

    // Clear a field's message as soon as the user edits it
    form.addEventListener("input", function (event) {
      if (event.target.id) clearError(event.target);
    });
  }

  function attachPasswordToggle(button) {
    var input = document.getElementById(button.dataset.toggle);
    if (!input) return;
    button.addEventListener("click", function () {
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      button.textContent = show ? "Hide password" : "Show password";
    });
  }

  function setupSearchPage(form) {
    var date = form.elements.date;
    date.min = todayLocal();
    if (!date.value) date.value = todayLocal();

    var swap = document.getElementById("swap-stations");
    if (swap) {
      swap.addEventListener("click", function () {
        var from = form.elements.source;
        var to = form.elements.destination;
        var temp = from.value;
        from.value = to.value;
        to.value = temp;
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form[data-form]").forEach(attachValidation);
    document.querySelectorAll("button[data-toggle]").forEach(attachPasswordToggle);
    var searchForm = document.querySelector('form[data-form="search"]');
    if (searchForm) setupSearchPage(searchForm);
  });
})();
