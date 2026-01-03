/**
 * Complete Routes Configuration for Dayflow HRMS
 * This file documents all routes in the system
 */

export interface Route {
  name: string
  path: string
  description: string
  requiresAuth?: boolean
  requiredRole?: "admin" | "employee" | "both"
}

export const ROUTES = {
  // Public Routes
  HOME: {
    name: "Home",
    path: "/",
    description: "Landing page with role selector",
    requiresAuth: false,
  },

  // Authentication Routes
  AUTH: {
    ADMIN_LOGIN: {
      name: "Admin Login",
      path: "/auth/admin/login",
      description: "Admin/HR personnel authentication",
      requiresAuth: false,
    },
    ADMIN_SIGNUP: {
      name: "Admin Sign Up",
      path: "/auth/admin/signup",
      description: "Admin/HR registration",
      requiresAuth: false,
    },
    EMPLOYEE_LOGIN: {
      name: "Employee Login",
      path: "/auth/employee/login",
      description: "Employee authentication",
      requiresAuth: false,
    },
    EMPLOYEE_SIGNUP: {
      name: "Employee Sign Up",
      path: "/auth/employee/signup",
      description: "Employee registration (disabled - admin only)",
      requiresAuth: false,
    },
    HR_LOGIN: {
      name: "HR Login",
      path: "/auth/hr/login",
      description: "HR authentication",
      requiresAuth: false,
    },
    HR_SIGNUP: {
      name: "HR Sign Up",
      path: "/auth/hr/signup",
      description: "HR registration",
      requiresAuth: false,
    },
  },

  // Dashboard Routes - Admin
  DASHBOARD_ADMIN: {
    ROOT: {
      name: "Admin Employees Directory",
      path: "/dashboard/admin",
      description: "Main admin dashboard showing all employees",
      requiresAuth: true,
      requiredRole: "admin",
    },
    ATTENDANCE: {
      name: "Admin Attendance",
      path: "/dashboard/admin/attendance",
      description: "Attendance tracking and reports for all employees",
      requiresAuth: true,
      requiredRole: "admin",
    },
    TIME_OFF: {
      name: "Admin Time Off",
      path: "/dashboard/admin/time-off",
      description: "Leave and time off management",
      requiresAuth: true,
      requiredRole: "admin",
    },
    PROFILE: {
      name: "Admin Profile",
      path: "/dashboard/admin/profile",
      description: "Admin profile and personal information",
      requiresAuth: true,
      requiredRole: "admin",
    },
  },

  // Dashboard Routes - Employee
  DASHBOARD_EMPLOYEE: {
    ROOT: {
      name: "Employee Dashboard",
      path: "/dashboard/employee",
      description: "Employee-specific dashboard view",
      requiresAuth: true,
      requiredRole: "employee",
    },
    ATTENDANCE: {
      name: "Employee Attendance",
      path: "/dashboard/employee/attendance",
      description: "Personal attendance records and history",
      requiresAuth: true,
      requiredRole: "employee",
    },
    TIME_OFF: {
      name: "Employee Time Off",
      path: "/dashboard/employee/time-off",
      description: "Request and manage personal time off",
      requiresAuth: true,
      requiredRole: "employee",
    },
    PROFILE: {
      name: "Employee Profile",
      path: "/dashboard/employee/profile",
      description: "Employee profile and personal information",
      requiresAuth: true,
      requiredRole: "employee",
    },
  },
}

/**
 * Get all routes as a flat array
 */
export function getAllRoutes(): Route[] {
  const routes: Route[] = []

  const walkRoutes = (obj: any) => {
    for (const key in obj) {
      const value = obj[key]
      if (value && typeof value === "object") {
        if (value.path && value.name) {
          routes.push(value)
        } else {
          walkRoutes(value)
        }
      }
    }
  }

  walkRoutes(ROUTES)
  return routes
}

/**
 * Filter routes by role
 */
export function getRoutesByRole(role: "admin" | "employee"): Route[] {
  return getAllRoutes().filter(
    (route) => !route.requiredRole || route.requiredRole === role || route.requiredRole === "both",
  )
}

/**
 * Get protected routes (requires authentication)
 */
export function getProtectedRoutes(): Route[] {
  return getAllRoutes().filter((route) => route.requiresAuth)
}

/**
 * Get public routes
 */
export function getPublicRoutes(): Route[] {
  return getAllRoutes().filter((route) => !route.requiresAuth)
}
