const express = require('express');
const app = express();
const port = 3000;
const path = require('path');
var methodOverride = require('method-override');
const axios = require('axios');
const session = require('express-session');

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(methodOverride('_method'));

// Session configuration
app.use(session({
    secret: 'your-secret-key-here',
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false, maxAge: 24 * 60 * 60 * 1000 } // 24 hours
}));

// API base URL
const API_BASE_URL = 'http://localhost:8000';

// Middleware to check authentication
const requireAuth = (req, res, next) => {
    if (req.session.accessToken) {
        next();
    } else {
        res.redirect('/login');
    }
};

app.get('/', (req,res)=> {
    res.render('index.ejs');
});

app.get("/login", (req, res) => {
    const error = req.session.error;
    req.session.error = null; // Clear error after displaying
    res.render("login.ejs", { error });
});

app.get("/signup", (req, res) => {
    const error = req.session.error;
    const success = req.session.success;
    req.session.error = null;
    req.session.success = null;
    res.render("signup.ejs", { error, success });
});

// Login POST route
app.post("/login", async (req, res) => {
    try {
        const { email, password, remember } = req.body;
        
        const response = await axios.post(`${API_BASE_URL}/auth/jwt/create/`, {
            email: email,
            password: password
        });

        if (response.data.access && response.data.refresh) {
            // Store tokens in session
            req.session.accessToken = response.data.access;
            req.session.refreshToken = response.data.refresh;
            req.session.userEmail = email;
            
            // If remember me is checked, extend cookie life
            if (remember) {
                req.session.cookie.maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days
            }
            
            res.redirect('/dashboard');
        } else {
            req.session.error = 'Invalid credentials';
            res.redirect('/login');
        }
    } catch (error) {
        console.error('Login error:', error.response?.data || error.message);
        req.session.error = 'Invalid email or password';
        res.redirect('/login');
    }
});

// Signup POST route
app.post("/signup", async (req, res) => {
    try {
        const { userid, email, password, role } = req.body;
        
        // Validate password requirements
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
        if (!passwordRegex.test(password)) {
            req.session.error = 'Password must be at least 8 characters with uppercase, lowercase, and number';
            return res.redirect('/signup');
        }
        
        const response = await axios.post(`${API_BASE_URL}/auth/users/`, {
            email: email,
            name: userid,
            password: password,
            re_password: password
        });

        if (response.status === 201 || response.status === 200) {
            req.session.success = 'Account created successfully! Please log in.';
            res.redirect('/login');
        } else {
            req.session.error = 'Failed to create account';
            res.redirect('/signup');
        }
    } catch (error) {
        console.error('Signup error:', error.response?.data || error.message);
        let errorMessage = 'Failed to create account';
        
        if (error.response?.data) {
            const errors = error.response.data;
            if (errors.email) {
                errorMessage = 'Email already exists or is invalid';
            } else if (errors.password) {
                errorMessage = 'Password requirements not met';
            }
        }
        
        req.session.error = errorMessage;
        res.redirect('/signup');
    }
});

// Logout route
app.post("/logout", (req, res) => {
    req.session.destroy((err) => {
        if (err) {
            console.error('Logout error:', err);
        }
        res.redirect('/login');
    });
});

// Password reset request
app.post("/forgot-password", async (req, res) => {
    try {
        const { email } = req.body;
        
        await axios.post(`${API_BASE_URL}/auth/users/reset_password/`, {
            email: email
        });
        
        req.session.success = 'Password reset email sent!';
        res.redirect('/login');
    } catch (error) {
        console.error('Password reset error:', error.response?.data || error.message);
        req.session.error = 'Failed to send password reset email';
        res.redirect('/login');
    }
});

// Protected routes
// app.get("/dashboard", requireAuth, (req, res) => {
//     res.render("dashboard.ejs", { userEmail: req.session.userEmail });
// });

// app.get("/trains", requireAuth, (req, res) => {
//     res.render("trains.ejs");
// });

// app.get('/reports', requireAuth, (req, res) => {
//     res.render('reports.ejs');
// });

// app.get('/settings', requireAuth, (req, res) => {
//     res.render('settings.ejs');
// });

app.get('/dashboard', (req,res)=> {
    res.render('dashboard.ejs');
});

app.get('/trains', (req, res) => {
    res.render('trains.ejs');
});
app.get('/reports', (req, res) => {
    res.render('reports.ejs');
});
app.get('/settings', (req, res) => {
    res.render('settings.ejs');
});

app.get('/service', requireAuth, (req, res) => {
    res.render('service.ejs');
});

app.get('/standby', requireAuth, (req, res) => {
    res.render('standby.ejs');
});

app.get("/maintenance", requireAuth, (req, res) => {
    res.render("maintenance.ejs");
});

app.get("/alerts", requireAuth, (req, res) => {
    res.render("alerts.ejs");
});

app.get("/schedule", requireAuth, (req, res) => {
    res.render("schedule.ejs");
});

app.get("/staff", requireAuth, (req, res) => {
    res.render("staff.ejs");
});

app.get("/fitness", (req,res)=> {
    res.render("input.ejs")
})

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});