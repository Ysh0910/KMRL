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
        axios.get(`${API_BASE_URL}/fitness_certificates/`)
            .then(response => {
                res.render('dashboard.ejs', { fitnessCertificates: response.data });
            })
            .catch(error => {
                console.error('Error fetching fitness certificates:', error.message);
                res.render('dashboard.ejs', { fitnessCertificates: [] });
            });
});

app.get('/trains', (req, res) => {
        axios.get(`${API_BASE_URL}/mileage/`)
            .then(response => {
                res.render('trains.ejs', { mileage: response.data });
            })
            .catch(error => {
                console.error('Error fetching mileage:', error.message);
                res.render('trains.ejs', { mileage: [] });
            });
});
app.get('/reports', (req, res) => {
    res.render('reports.ejs');
});
app.get('/settings', (req, res) => {
    res.render('settings.ejs');
});

app.get('/service',  (req, res) => {
    res.render('service.ejs');
});

app.get('/standby',  (req, res) => {
    res.render('standby.ejs');
});

app.get("/maintenance",  (req, res) => {
        axios.get(`${API_BASE_URL}/joboards/`)
            .then(response => {
                res.render("maintenance.ejs", { jobCards: response.data });
            })
            .catch(error => {
                console.error('Error fetching job cards:', error.message);
                res.render("maintenance.ejs", { jobCards: [] });
            });
});

app.get("/alerts",  (req, res) => {
    res.render("alerts.ejs");
});

app.get("/schedule", (req, res) => {
            axios.post(`${API_BASE_URL}/getpredictions/`)
                .then(response => {
                    res.render("schedule.ejs", { predictions: response.data });
                })
                .catch(error => {
                    console.error('Error fetching predictions:', error.message);
                    res.render("schedule.ejs", { predictions: {} });
                });
//             axios.post(`${API_BASE_URL}/getpredictions/`, {
//   fitness_certificates: {
//     "0": true, "1": true, "2": true, "3": true, "4": true,
//     "5": false, "6": true, "7": true, "8": false, "9": true,
//     "10": true, "11": true, "12": false, "13": true, "14": true,
//     "15": true, "16": false, "17": true, "18": false, "19": true,
//     "20": true, "21": true, "22": true, "23": true, "24": false
//   },
//   job_cards: {
//     "0": "COMPLETED", "1": "INPROGRESS", "2": "COMPLETED", "3": "INPROGRESS", "4": "COMPLETED",
//     "5": "COMPLETED", "6": "COMPLETED", "7": "COMPLETED", "8": "COMPLETED", "9": "COMPLETED",
//     "10": "INPROGRESS", "11": "COMPLETED", "12": "INPROGRESS", "13": "COMPLETED", "14": "INPROGRESS",
//     "15": "COMPLETED", "16": "COMPLETED", "17": "COMPLETED", "18": "COMPLETED", "19": "COMPLETED",
//     "20": "COMPLETED", "21": "COMPLETED", "22": "INPROGRESS", "23": "INPROGRESS", "24": "COMPLETED"
//   },
//   branding_priority: {
//     "0": 2, "1": 3, "2": 3, "3": 3, "4": 1,
//     "5": 3, "6": 3, "7": 0, "8": 3, "9": 3,
//     "10": 0, "11": 3, "12": 0, "13": 1, "14": 2,
//     "15": 1, "16": 1, "17": 0, "18": 1, "19": 0,
//     "20": 3, "21": 2, "22": 0, "23": 2, "24": 1
//   },
//   current_mileage: {
//     "0": 11794, "1": 14108, "2": 34759, "3": 43713, "4": 24540,
//     "5": 46170, "6": 20618, "7": 44674, "8": 38474, "9": 25519,
//     "10": 14670, "11": 43083, "12": 46581, "13": 16176, "14": 14787,
//     "15": 40948, "16": 12268, "17": 40026, "18": 42357, "19": 20693,
//     "20": 25369, "21": 32165, "22": 43456, "23": 43912, "24": 44504
//   }
// })

});
// API endpoint for dashboard AJAX fetch
app.get('/dashboard-data', (req, res) => {
    axios.get(`${API_BASE_URL}/fitness_certificates/`)
        .then(response => {
            res.json(response.data);
        })
        .catch(error => {
            console.error('Error fetching fitness certificates:', error.message);
            res.status(500).json([]);
        });
});

app.get("/staff", (req, res) => {
    res.render("staff.ejs");
});

app.get("/fitness", (req,res)=> {
    res.render("input.ejs")
})

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});