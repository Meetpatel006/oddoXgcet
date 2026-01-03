"use client"

import { useState, useEffect } from "react"
import { Plane, Plus, Mail, Briefcase, Building2, Calendar, User, Phone, MapPin, Globe, Heart, CreditCard, Shield, AlertCircle } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface Employee {
  id: string
  name: string
  email: string
  image: string
  status: "present" | "absent" | "leave" | "pending"
  jobPosition: string
  department: string
  dateOfJoining: string
  // Resume/Private Info
  dateOfBirth?: string
  residingAddress?: string
  nationality?: string
  personalEmail?: string
  gender?: string
  maritalStatus?: string
  mobile?: string
  // Company Info
  company?: string
  manager?: string
  location?: string
  // Bank Details
  accountNumber?: string
  bankName?: string
  ifscCode?: string
  panNo?: string
  uanNo?: string
  empCode?: string
}

// Mock employee data removed - fetching from API

const getStatusColor = (status: string) => {
  switch (status) {
    case "present":
      return "bg-green-500"
    case "absent":
      return "bg-yellow-500"
    case "leave":
      return "bg-blue-500"
    case "pending":
      return "bg-gray-400"
    default:
      return "bg-gray-300"
  }
}

const renderStatusBadge = (status: string) => {
  switch (status) {
    case "present":
      return (
        <Badge className="bg-green-500/10 text-green-700 border-green-200 hover:bg-green-500/20">
          <div className="w-2 h-2 rounded-full bg-green-500 mr-1" />
          Present
        </Badge>
      )
    case "absent":
      return (
        <Badge className="bg-yellow-500/10 text-yellow-700 border-yellow-200 hover:bg-yellow-500/20">
          <div className="w-2 h-2 rounded-full bg-yellow-500 mr-1" />
          Absent
        </Badge>
      )
    case "leave":
      return (
        <Badge className="bg-blue-500/10 text-blue-700 border-blue-200 hover:bg-blue-500/20">
          <Plane className="w-3 h-3 mr-1" />
          On Leave
        </Badge>
      )
    case "pending":
      return (
        <Badge className="bg-gray-500/10 text-gray-700 border-gray-200 hover:bg-gray-500/20">
          <div className="w-2 h-2 rounded-full bg-gray-500 mr-1" />
          Pending
        </Badge>
      )
    default:
      return null
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case "present":
      return "Present"
    case "absent":
      return "Absent"
    case "leave":
      return "On Leave"
    case "pending":
      return "Pending"
    default:
      return "Unknown"
  }
}

export default function AdminDashboard() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null)
  const [isProfileOpen, setIsProfileOpen] = useState(false)
  const [isNewEmployeeOpen, setIsNewEmployeeOpen] = useState(false)
  const [newEmployeeData, setNewEmployeeData] = useState<Partial<Employee>>({})

  // New state for API data
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const fetchEmployees = async () => {
      try {
        const token = localStorage.getItem("access_token")
        const response = await fetch("http://localhost:8000/api/v1/employees/", {
          headers: {
            "Authorization": `Bearer ${token}`
          }
        })
        
        if (response.ok) {
            const data = await response.json()
            
            const mappedEmployees: Employee[] = data.map((emp: any) => ({
              id: emp.id.toString(),
              name: `${emp.first_name} ${emp.last_name}`,
              email: emp.email,
              image: emp.profile_picture || "/employee-avatar.png",
              status: emp.status || "pending",
              jobPosition: emp.designation || "N/A",
              department: emp.department || "N/A",
              dateOfJoining: emp.joining_date || "N/A",
              dateOfBirth: emp.date_of_birth,
              residingAddress: emp.address,
              nationality: emp.nationality,
              personalEmail: emp.personal_email,
              gender: emp.gender,
              maritalStatus: emp.marital_status,
              mobile: emp.phone,
              company: "TechCorp Inc.", // Placeholder
              manager: emp.manager_id ? `Manager #${emp.manager_id}` : "N/A",
              location: "N/A",
              empCode: emp.employee_id
            }))
            setEmployees(mappedEmployees)
        } else {
            console.error("Failed to fetch employees:", response.statusText)
        }
      } catch (err: any) {
        console.error("Error fetching employees:", err)
        setError("Failed to load employees")
      } finally {
        setLoading(false)
      }
    }
    
    fetchEmployees()
  }, [])

  const filteredEmployees = employees.filter(
    (emp) =>
      emp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emp.email.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const handleEmployeeClick = (employee: Employee) => {
    setSelectedEmployee(employee)
    setIsProfileOpen(true)
  }

  const handleNewEmployee = () => {
    setNewEmployeeData({})
    setIsNewEmployeeOpen(true)
  }

  const handleAddEmployee = () => {
    // TODO: Implement add employee logic
    console.log("Adding new employee:", newEmployeeData)
    setIsNewEmployeeOpen(false)
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header Section */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground mb-2">Employee Management</h1>
        <p className="text-muted-foreground">
          View and manage all employees in your organization. Click on any employee card to view detailed information,
          or use the NEW button to add a new employee to the system.
        </p>
      </div>

      {/* NEW Button & Search Bar */}
      <div className="bg-muted/30 border border-border rounded-lg p-4 mb-8">
        <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
          <button 
            onClick={handleNewEmployee}
            className="flex items-center justify-center gap-2 px-6 py-2.5 bg-purple-500 text-white rounded-md hover:bg-purple-600 transition font-medium shadow-sm"
          >
            <Plus className="w-4 h-4" />
            NEW
          </button>
          <input
            suppressHydrationWarning
            type="text"
            placeholder="Search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2.5 rounded-full border border-border bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary text-center"
          />
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-12 text-destructive">
          <p>{error}</p>
        </div>
      )}

      {/* Employee Cards Grid */}
      {!loading && !error && (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredEmployees.map((employee) => (
          <Card
            key={employee.id}
            onClick={() => handleEmployeeClick(employee)}
            className="hover:shadow-xl hover:border-primary/50 hover:scale-[1.02] transition-all duration-200 cursor-pointer group overflow-hidden"
          >
            <CardContent className="p-0">
              {/* Header with gradient background */}
              <div className="bg-gradient-to-br from-primary/5 via-primary/10 to-primary/5 p-6 pb-4">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <img
                        src={employee.image || "/placeholder.svg"}
                        alt={employee.name}
                        className="w-16 h-16 rounded-full object-cover border-4 border-background shadow-lg group-hover:border-primary/30 transition-colors"
                        onError={(e) => {
                          e.currentTarget.src = "/placeholder.svg"
                        }}
                      />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-foreground truncate">{employee.name}</h3>
                      <div className="flex items-center gap-1.5 text-sm text-muted-foreground mt-0.5">
                        <Briefcase className="w-3.5 h-3.5" />
                        <p className="truncate">{employee.jobPosition}</p>
                      </div>
                    </div>
                  </div>
                  {renderStatusBadge(employee.status)}
                </div>
              </div>

              {/* Employee Details */}
              <div className="p-6 pt-4 space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <Mail className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground truncate">{employee.email}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Building2 className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">{employee.department}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Joined {employee.dateOfJoining}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      )}

      {/* Empty State */}
      {filteredEmployees.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No employees found matching your search.</p>
        </div>
      )}

      {/* Employee Profile Dialog */}
      <Dialog open={isProfileOpen} onOpenChange={setIsProfileOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl">My Profile</DialogTitle>
          </DialogHeader>
          {selectedEmployee && (
            <div className="space-y-6">
              {/* Profile Header */}
              <div className="flex items-center gap-6 pb-6 border-b">
                <img
                  src={selectedEmployee.image || "/placeholder.svg"}
                  alt={selectedEmployee.name}
                  className="w-24 h-24 rounded-full object-cover border-4 border-primary/20"
                />
                <div className="flex-1 space-y-3">
                  <div>
                    <h2 className="text-2xl font-bold">{selectedEmployee.name}</h2>
                    <p className="text-muted-foreground">{selectedEmployee.jobPosition}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Company</p>
                      <p className="font-medium">{selectedEmployee.company || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Department</p>
                      <p className="font-medium">{selectedEmployee.department}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Manager</p>
                      <p className="font-medium">{selectedEmployee.manager || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Location</p>
                      <p className="font-medium">{selectedEmployee.location || "N/A"}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <Tabs defaultValue="resume" className="w-full">
                <TabsList className="w-full justify-start">
                  <TabsTrigger value="resume">Resume</TabsTrigger>
                  <TabsTrigger value="private">Private Info</TabsTrigger>
                  <TabsTrigger value="salary">Salary Info</TabsTrigger>
                  <TabsTrigger value="security">Security</TabsTrigger>
                </TabsList>

                <TabsContent value="resume" className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Date of Birth</Label>
                      <p className="font-medium">{selectedEmployee.dateOfBirth || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Date of Joining</Label>
                      <p className="font-medium">{selectedEmployee.dateOfJoining}</p>
                    </div>
                    <div className="space-y-2 col-span-2">
                      <Label className="text-muted-foreground">Residing Address</Label>
                      <p className="font-medium">{selectedEmployee.residingAddress || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Nationality</Label>
                      <p className="font-medium">{selectedEmployee.nationality || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Gender</Label>
                      <p className="font-medium">{selectedEmployee.gender || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Marital Status</Label>
                      <p className="font-medium">{selectedEmployee.maritalStatus || "N/A"}</p>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="private" className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Personal Email</Label>
                      <p className="font-medium">{selectedEmployee.personalEmail || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Mobile</Label>
                      <p className="font-medium">{selectedEmployee.mobile || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Work Email</Label>
                      <p className="font-medium">{selectedEmployee.email}</p>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="salary" className="space-y-4 mt-4">
                  <h3 className="font-semibold text-lg mb-4">Bank Details</h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Account Number</Label>
                      <p className="font-medium">{selectedEmployee.accountNumber || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Bank Name</Label>
                      <p className="font-medium">{selectedEmployee.bankName || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">IFSC Code</Label>
                      <p className="font-medium">{selectedEmployee.ifscCode || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">PAN No</Label>
                      <p className="font-medium">{selectedEmployee.panNo || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">UAN No</Label>
                      <p className="font-medium">{selectedEmployee.uanNo || "N/A"}</p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-muted-foreground">Emp Code</Label>
                      <p className="font-medium">{selectedEmployee.empCode || "N/A"}</p>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="security" className="space-y-4 mt-4">
                  <div className="text-muted-foreground">
                    Security settings and access control information would be displayed here.
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* New Employee Dialog */}
      <Dialog open={isNewEmployeeOpen} onOpenChange={setIsNewEmployeeOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl">Add New Employee</DialogTitle>
            <DialogDescription>
              Fill in the employee details below. All fields marked with * are required.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Important Note */}
            <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div className="space-y-2 text-sm">
                  <p className="font-semibold text-yellow-900">Note</p>
                  <ul className="space-y-1 text-yellow-800">
                    <li>• Normal users cannot register, so when the HR officer or Admin creates a new user/employee, their ID should also be created with this method.</li>
                    <li>• The password will be auto-generated for the first time by the system.</li>
                    <li>• Employees can login and change the system-generated password.</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Form */}
            <div className="space-y-6">
              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name *</Label>
                    <Input
                      id="name"
                      placeholder="Enter full name"
                      value={newEmployeeData.name || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Work Email *</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="employee@company.com"
                      value={newEmployeeData.email || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, email: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="jobPosition">Job Position *</Label>
                    <Input
                      id="jobPosition"
                      placeholder="e.g., Software Engineer"
                      value={newEmployeeData.jobPosition || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, jobPosition: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department">Department *</Label>
                    <Input
                      id="department"
                      placeholder="e.g., Engineering"
                      value={newEmployeeData.department || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, department: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="mobile">Mobile *</Label>
                    <Input
                      id="mobile"
                      placeholder="+1 (555) 000-0000"
                      value={newEmployeeData.mobile || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, mobile: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="dateOfJoining">Date of Joining *</Label>
                    <Input
                      id="dateOfJoining"
                      type="date"
                      value={newEmployeeData.dateOfJoining || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, dateOfJoining: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Personal Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="dateOfBirth">Date of Birth</Label>
                    <Input
                      id="dateOfBirth"
                      type="date"
                      value={newEmployeeData.dateOfBirth || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, dateOfBirth: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gender">Gender</Label>
                    <Input
                      id="gender"
                      placeholder="Male/Female/Other"
                      value={newEmployeeData.gender || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, gender: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="nationality">Nationality</Label>
                    <Input
                      id="nationality"
                      placeholder="e.g., American"
                      value={newEmployeeData.nationality || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, nationality: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="maritalStatus">Marital Status</Label>
                    <Input
                      id="maritalStatus"
                      placeholder="Single/Married"
                      value={newEmployeeData.maritalStatus || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, maritalStatus: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2 col-span-2">
                    <Label htmlFor="residingAddress">Residing Address</Label>
                    <Input
                      id="residingAddress"
                      placeholder="Full address"
                      value={newEmployeeData.residingAddress || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, residingAddress: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="personalEmail">Personal Email</Label>
                    <Input
                      id="personalEmail"
                      type="email"
                      placeholder="personal@email.com"
                      value={newEmployeeData.personalEmail || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, personalEmail: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Company Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="company">Company</Label>
                    <Input
                      id="company"
                      placeholder="Company name"
                      value={newEmployeeData.company || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, company: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="manager">Manager</Label>
                    <Input
                      id="manager"
                      placeholder="Manager name"
                      value={newEmployeeData.manager || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, manager: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="location">Location</Label>
                    <Input
                      id="location"
                      placeholder="Office location"
                      value={newEmployeeData.location || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, location: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="empCode">Employee Code</Label>
                    <Input
                      id="empCode"
                      placeholder="EMP001"
                      value={newEmployeeData.empCode || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, empCode: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-semibold text-lg">Bank Details</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="accountNumber">Account Number</Label>
                    <Input
                      id="accountNumber"
                      placeholder="Bank account number"
                      value={newEmployeeData.accountNumber || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, accountNumber: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bankName">Bank Name</Label>
                    <Input
                      id="bankName"
                      placeholder="Name of the bank"
                      value={newEmployeeData.bankName || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, bankName: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ifscCode">IFSC Code</Label>
                    <Input
                      id="ifscCode"
                      placeholder="Bank IFSC code"
                      value={newEmployeeData.ifscCode || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, ifscCode: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="panNo">PAN No</Label>
                    <Input
                      id="panNo"
                      placeholder="PAN number"
                      value={newEmployeeData.panNo || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, panNo: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="uanNo">UAN No</Label>
                    <Input
                      id="uanNo"
                      placeholder="Universal Account Number"
                      value={newEmployeeData.uanNo || ""}
                      onChange={(e) => setNewEmployeeData({ ...newEmployeeData, uanNo: e.target.value })}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                onClick={() => setIsNewEmployeeOpen(false)}
                className="px-6 py-2 border border-border rounded-lg hover:bg-muted transition"
              >
                Cancel
              </button>
              <button
                onClick={handleAddEmployee}
                className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
              >
                Add Employee
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
