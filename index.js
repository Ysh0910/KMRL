const express = require('express');
const app = express();
const port = 3000;
const path = require('path');
var methodOverride = require('method-override');

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));
app.use(express.urlencoded({ extended: true }));
app.use(methodOverride('_method'));

app.get('/', (req,res)=> {
    res.render('index.ejs');
});

app.get("/login", (req, res) => {
    res.render("login.ejs");
});

app.get("/signup", (req, res) => {
    res.render("signup.ejs");
});

app.get("/dashboard", (req, res) => {
    res.render("dashboard.ejs");
});

app.get("/trains", (req, res) => {
    res.render("trains.ejs");
});

app.get('/reports', (req, res) => {
    res.render('reports.ejs');
});

app.get('/settings', (req, res) => {
    res.render('settings.ejs');
});

app.get('/service', (req, res) => {
    res.render('service.ejs');
});

app.get('/standby', (req, res) => {
    res.render('standby.ejs');
});

app.get("/maintenance", (req, res) => {
    res.render("maintenance.ejs");
});

app.get("/alerts", (req, res) => {
    res.render("alerts.ejs");
});

app.get("/schedule", (req, res) => {
    res.render("schedule.ejs");
});

app.get("/staff", (req, res) => {
    res.render("staff.ejs");
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});