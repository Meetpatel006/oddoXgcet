"use client"

import { useState, useEffect } from "react"
import { Edit, User, Mail, Phone, Building2, MapPin, Briefcase, AlertCircle, Save, X, Upload, FileText, Award, Eye } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export default function AdminProfile() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [profileData, setProfileData] = useState<any>(null)
  const [formData, setFormData] = useState<any>({})
  const [uploading, setUploading] = useState(false)
  const [salaryStructure, setSalaryStructure] = useState<any>({
    basic_salary: 0,
    hra: 0,
    standard_allowance: 0,
    performance_bonus: 0,
    lta: 0,
    fixed_allowance: 0,
    professional_tax: 0,
    pf_contribution: 0,
  })

  const [salaryConfig, setSalaryConfig] = useState({
    monthlyWage: 0,
    basicPercent: 50,
    hraPercent: 50,
    standardAllowancePercent: 0,
    performanceBonusPercent: 0,
    ltaPercent: 0,
    pfPercent: 12,
    professionalTax: 200
  })

  // Recalculate salary structure when config changes
  useEffect(() => {
    if (!isEditing) return

    const wage = Number(salaryConfig.monthlyWage) || 0
    const basic = (wage * (Number(salaryConfig.basicPercent) || 0)) / 100
    const hra = (basic * (Number(salaryConfig.hraPercent) || 0)) / 100
    const std = (wage * (Number(salaryConfig.standardAllowancePercent) || 0)) / 100
    const perf = (basic * (Number(salaryConfig.performanceBonusPercent) || 0)) / 100
    const lta = (basic * (Number(salaryConfig.ltaPercent) || 0)) / 100

    const totalAllocated = basic + hra + std + perf + lta
    const fixed = Math.max(0, wage - totalAllocated)

    const pf = (basic * (Number(salaryConfig.pfPercent) || 0)) / 100

    setSalaryStructure((prev: any) => ({
      ...prev,
      basic_salary: basic,
      hra: hra,
      standard_allowance: std,
      performance_bonus: perf,
      lta: lta,
      fixed_allowance: fixed,
      professional_tax: Number(salaryConfig.professionalTax) || 0,
      pf_contribution: pf,
    }))
  }, [salaryConfig, isEditing])

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) return

      const data = await api.get("/employees/me", token)

      // Merge API data with mock data for fields not yet in API
      const mergedData = {
        ...data,
        // Mock data for Resume
        about: "Experienced HR professional with over 10 years in talent management and organizational development. Passionate about creating positive workplace cultures and driving employee engagement initiatives.",
        whatILove: "I love fostering a collaborative environment where every team member feels valued and empowered. Building strong relationships and helping people reach their full potential is what drives me every day.",
        interests: "Leadership development, organizational psychology, team building activities, professional coaching, and staying updated with the latest HR technology trends.",
        skills: ["Leadership", "Communication", "Strategic Planning", "Employee Relations", "Performance Management"],
        // Mock data for Salary (will be replaced by real data if available)
        workingDaysPerWeek: 5,
        breakTime: "1 hour",
      }

      setProfileData(mergedData)
      setFormData({
        first_name: data.first_name,
        last_name: data.last_name,
        phone: data.phone || "",
        personal_email: data.personal_email || "",
        date_of_birth: data.date_of_birth || "",
        gender: data.gender || "",
        marital_status: data.marital_status || "",
        nationality: data.nationality || "",
        address: data.address || "",
      })

      // Fetch Salary Structure
      try {
        const salaryData = await api.get("/salary/me", token)
        if (salaryData) {
          setSalaryStructure(salaryData)

          // Reverse calculate config
          const totalEarnings = Number(salaryData.basic_salary) + Number(salaryData.hra) + Number(salaryData.standard_allowance) + Number(salaryData.performance_bonus) + Number(salaryData.lta) + Number(salaryData.fixed_allowance)
          const basic = Number(salaryData.basic_salary)

          setSalaryConfig({
            monthlyWage: totalEarnings,
            basicPercent: totalEarnings ? (basic / totalEarnings) * 100 : 50,
            hraPercent: basic ? (Number(salaryData.hra) / basic) * 100 : 50,
            standardAllowancePercent: totalEarnings ? (Number(salaryData.standard_allowance) / totalEarnings) * 100 : 0,
            performanceBonusPercent: basic ? (Number(salaryData.performance_bonus) / basic) * 100 : 0,
            ltaPercent: basic ? (Number(salaryData.lta) / basic) * 100 : 0,
            pfPercent: basic ? (Number(salaryData.pf_contribution) / basic) * 100 : 12,
            professionalTax: Number(salaryData.professional_tax)
          })
        }
      } catch (err) {
        console.log("No salary structure found, using defaults")
      }

    } catch (error: any) {
      toast({
        title: "Error",
        description: "Failed to fetch profile data",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleConfigChange = (field: string, value: string) => {
    setSalaryConfig(prev => ({ ...prev, [field]: parseFloat(value) || 0 }))
  }


  const handleUpdate = async () => {
    try {
      const token = localStorage.getItem("token")
      if (!token) return

      // 1. Update Profile
      const updatePayload = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone,
        personal_email: formData.personal_email,
        date_of_birth: formData.date_of_birth || null,
        gender: formData.gender || null,
        marital_status: formData.marital_status || null,
        nationality: formData.nationality,
        address: formData.address,
      }

      const updatedProfile = await api.put(`/employees/${profileData.id}`, updatePayload, token)
      setProfileData({ ...profileData, ...updatedProfile })

      // 2. Update Salary Structure
      if (salaryStructure.id) {
        const salaryPayload = {
          basic_salary: Number(salaryStructure.basic_salary),
          hra: Number(salaryStructure.hra),
          standard_allowance: Number(salaryStructure.standard_allowance),
          performance_bonus: Number(salaryStructure.performance_bonus),
          lta: Number(salaryStructure.lta),
          fixed_allowance: Number(salaryStructure.fixed_allowance),
          professional_tax: Number(salaryStructure.professional_tax),
          pf_contribution: Number(salaryStructure.pf_contribution),
        }
        const updatedSalary = await api.put(`/salary/structure/${salaryStructure.id}`, salaryPayload, token)
        setSalaryStructure(updatedSalary)
      } else {
        try {
          const salaryPayload = {
            employee_profile_id: profileData.id,
            basic_salary: Number(salaryStructure.basic_salary),
            hra: Number(salaryStructure.hra),
            standard_allowance: Number(salaryStructure.standard_allowance),
            performance_bonus: Number(salaryStructure.performance_bonus),
            lta: Number(salaryStructure.lta),
            fixed_allowance: Number(salaryStructure.fixed_allowance),
            professional_tax: Number(salaryStructure.professional_tax),
            pf_contribution: Number(salaryStructure.pf_contribution),
          }
          const newSalary = await api.post("/salary/structure", salaryPayload, token)
          setSalaryStructure(newSalary)
        } catch (e) {
          console.error("Failed to create salary structure", e)
        }
      }

      setIsEditing(false)
      toast({
        title: "Success",
        description: "Profile and Salary updated successfully",
      })
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to update profile",
        variant: "destructive",
      })
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData({ ...formData, [field]: value })
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, type: 'profile-picture' | 'resume' | 'certification') => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)

    try {
      const token = localStorage.getItem("token")
      if (!token) return

      const response = await fetch(`http://localhost:8000/api/v1/upload/${type}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      if (!response.ok) throw new Error('Upload failed')

      const data = await response.json()

      if (type === 'profile-picture') {
        setProfileData({ ...profileData, profile_picture: `http://localhost:8000${data.url}` })
        await api.put(`/employees/${profileData.id}`, { profile_picture: `http://localhost:8000${data.url}` }, token)
        toast({ title: "Success", description: "Profile picture updated" })
      } else if (type === 'resume') {
        setProfileData({ ...profileData, resume_url: `http://localhost:8000${data.url}` })
        await api.put(`/employees/${profileData.id}`, { resume_url: `http://localhost:8000${data.url}` }, token)
        toast({ title: "Success", description: "Resume uploaded" })
      } else if (type === 'certification') {
        // Add the new certification to the list
        const newCert = {
          name: file.name.replace(/\.[^/.]+$/, ""), // Remove file extension for display name
          certificate_url: `http://localhost:8000${data.url}`,
          issue_date: new Date().toISOString().split('T')[0]
        }
        const updatedCerts = [...(profileData.certifications || []), newCert]
        setProfileData({ ...profileData, certifications: updatedCerts })
        toast({ title: "Success", description: "Certification uploaded" })
      }

    } catch (error) {
      console.error(error)
      toast({ title: "Error", description: "File upload failed", variant: "destructive" })
    } finally {
      setUploading(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-center">Loading profile...</div>
  }

  if (!profileData) {
    return <div className="p-8 text-center">Failed to load profile data.</div>
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header Section */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">My Profile</h1>
          <p className="text-muted-foreground">
            View and manage your profile information, including personal details, resume, and salary information.
          </p>
        </div>
        <div>
          {isEditing ? (
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                <X className="w-4 h-4 mr-2" /> Cancel
              </Button>
              <Button onClick={handleUpdate}>
                <Save className="w-4 h-4 mr-2" /> Save Changes
              </Button>
            </div>
          ) : (
            <Button onClick={() => setIsEditing(true)}>
              <Edit className="w-4 h-4 mr-2" /> Edit Profile
            </Button>
          )}
        </div>
      </div>

      {/* Profile Card */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Left Side - Profile Picture */}
            <div className="flex flex-col items-center md:items-start">
              <div className="relative">
                <img
                  src={profileData.profile_picture || "/placeholder.svg"}
                  alt={`${profileData.first_name} ${profileData.last_name}`}
                  className="w-32 h-32 rounded-full object-cover border-4 border-primary/20"
                  onError={(e) => {
                    e.currentTarget.src = "/placeholder.svg"
                  }}
                />
                <input
                  type="file"
                  id="profile-upload"
                  className="hidden"
                  accept="image/*"
                  onChange={(e) => handleFileUpload(e, 'profile-picture')}
                  disabled={uploading}
                />
              </div>
              {/* View and Upload buttons for profile picture */}
              <div className="flex gap-2 mt-3">
                {profileData.profile_picture && (
                  <Button variant="outline" size="sm" asChild>
                    <a href={profileData.profile_picture} target="_blank" rel="noopener noreferrer">
                      <Eye className="w-4 h-4 mr-1" /> View
                    </a>
                  </Button>
                )}
                <Button size="sm" onClick={() => document.getElementById('profile-upload')?.click()} disabled={uploading}>
                  <Upload className="w-4 h-4 mr-1" /> {uploading ? "..." : "Upload"}
                </Button>
              </div>
            </div>

            {/* Middle - Personal Info */}
            <div className="flex-1 space-y-4">
              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">Name</Label>
                {isEditing ? (
                  <div className="flex gap-2">
                    <Input
                      value={formData.first_name}
                      onChange={(e) => handleInputChange("first_name", e.target.value)}
                      placeholder="First Name"
                    />
                    <Input
                      value={formData.last_name}
                      onChange={(e) => handleInputChange("last_name", e.target.value)}
                      placeholder="Last Name"
                    />
                  </div>
                ) : (
                  <p className="text-2xl font-bold text-foreground">{profileData.first_name} {profileData.last_name}</p>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Login ID</Label>
                  <p className="font-medium">{profileData.employee_id}</p>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Work Email</Label>
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-muted-foreground" />
                    <p className="font-medium">{profileData.email}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Mobile</Label>
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-muted-foreground" />
                    {isEditing ? (
                      <Input
                        value={formData.phone}
                        onChange={(e) => handleInputChange("phone", e.target.value)}
                      />
                    ) : (
                      <p className="font-medium">{profileData.phone || "N/A"}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Side - Company Info */}
            <div className="flex-1 space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Company ID</Label>
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-muted-foreground" />
                    <p className="font-medium">{profileData.company_id}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Department</Label>
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-muted-foreground" />
                    <p className="font-medium">{profileData.department || "N/A"}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Designation</Label>
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-muted-foreground" />
                    <p className="font-medium">{profileData.designation || "N/A"}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Joining Date</Label>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <p className="font-medium">{profileData.joining_date || "N/A"}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs Section */}
      <Tabs defaultValue="resume" className="w-full">
        <TabsList className="w-full justify-start mb-6">
          <TabsTrigger value="resume">Resume</TabsTrigger>
          <TabsTrigger value="certifications">Certifications</TabsTrigger>
          <TabsTrigger value="private">Private Info</TabsTrigger>
          <TabsTrigger value="salary">Salary Info</TabsTrigger>
        </TabsList>

        {/* Resume Tab */}
        <TabsContent value="resume" className="space-y-6">
          <Card className="mb-6">
            <CardContent className="p-6 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary/10 rounded-lg">
                  <FileText className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">Resume</h3>
                  <p className="text-sm text-muted-foreground">
                    {profileData.resume_url ? "Resume uploaded" : "No resume uploaded"}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                {profileData.resume_url && (
                  <Button variant="outline" asChild>
                    <a href={profileData.resume_url} target="_blank" rel="noopener noreferrer">
                      <Eye className="w-4 h-4 mr-1" /> View
                    </a>
                  </Button>
                )}
                <div className="relative">
                  <input
                    type="file"
                    id="resume-upload"
                    className="hidden"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => handleFileUpload(e, 'resume')}
                    disabled={uploading}
                  />
                  <Button onClick={() => document.getElementById('resume-upload')?.click()} disabled={uploading}>
                    <Upload className="w-4 h-4 mr-2" />
                    {uploading ? "Uploading..." : "Upload New"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* About Section */}
            <Card>
              <CardContent className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    About
                    <Edit className="w-4 h-4 text-muted-foreground cursor-pointer hover:text-foreground" />
                  </h3>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">{profileData.about}</p>
              </CardContent>
            </Card>

            {/* Skills Section */}
            <Card>
              <CardContent className="p-6 space-y-4">
                <h3 className="text-lg font-semibold">Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {profileData.skills.map((skill: string, index: number) => (
                    <Badge key={index} variant="outline" className="bg-primary/10 text-primary border-primary/20">
                      {skill}
                    </Badge>
                  ))}
                  <button className="px-3 py-1 text-xs border border-dashed border-muted-foreground rounded-md text-muted-foreground hover:text-foreground hover:border-foreground transition">
                    + Add Skill
                  </button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* What I love about my job */}
          <Card>
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  What I love about my job
                  <Edit className="w-4 h-4 text-muted-foreground cursor-pointer hover:text-foreground" />
                </h3>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{profileData.whatILove}</p>
            </CardContent>
          </Card>

          {/* My interests and hobbies */}
          <Card>
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  My interests and hobbies
                  <Edit className="w-4 h-4 text-muted-foreground cursor-pointer hover:text-foreground" />
                </h3>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{profileData.interests}</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Certifications Tab */}
        <TabsContent value="certifications" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Certifications</CardTitle>
              <div className="relative">
                <input
                  type="file"
                  id="cert-upload"
                  className="hidden"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => handleFileUpload(e, 'certification')}
                  disabled={uploading}
                />
                <Button onClick={() => document.getElementById('cert-upload')?.click()} disabled={uploading}>
                  <Upload className="w-4 h-4 mr-2" />
                  Add Certification
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {profileData.certifications && profileData.certifications.length > 0 ? (
                <div className="grid gap-4">
                  {profileData.certifications.map((cert: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-primary/10 rounded">
                          <FileText className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <h4 className="font-medium">{cert.name}</h4>
                          <p className="text-sm text-muted-foreground">{cert.issue_date}</p>
                        </div>
                      </div>
                      {cert.certificate_url && (
                        <Button variant="outline" size="sm" asChild>
                          <a href={cert.certificate_url} target="_blank" rel="noopener noreferrer">
                            <Eye className="w-4 h-4 mr-1" /> View
                          </a>
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No certifications added yet.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Private Info Tab */}
        <TabsContent value="private">
          <Card>
            <CardHeader>
              <CardTitle>Private Information</CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Personal Email</Label>
                  {isEditing ? (
                    <Input
                      value={formData.personal_email}
                      onChange={(e) => handleInputChange("personal_email", e.target.value)}
                      type="email"
                    />
                  ) : (
                    <p className="font-medium p-2 bg-muted rounded-md">{profileData.personal_email || "N/A"}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Date of Birth</Label>
                  {isEditing ? (
                    <Input
                      value={formData.date_of_birth}
                      onChange={(e) => handleInputChange("date_of_birth", e.target.value)}
                      type="date"
                    />
                  ) : (
                    <p className="font-medium p-2 bg-muted rounded-md">{profileData.date_of_birth || "N/A"}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Gender</Label>
                  {isEditing ? (
                    <Select
                      value={formData.gender}
                      onValueChange={(value) => handleInputChange("gender", value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Gender" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="male">Male</SelectItem>
                        <SelectItem value="female">Female</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  ) : (
                    <p className="font-medium p-2 bg-muted rounded-md capitalize">{profileData.gender || "N/A"}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Marital Status</Label>
                  {isEditing ? (
                    <Select
                      value={formData.marital_status}
                      onValueChange={(value) => handleInputChange("marital_status", value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="single">Single</SelectItem>
                        <SelectItem value="married">Married</SelectItem>
                        <SelectItem value="divorced">Divorced</SelectItem>
                        <SelectItem value="widowed">Widowed</SelectItem>
                      </SelectContent>
                    </Select>
                  ) : (
                    <p className="font-medium p-2 bg-muted rounded-md capitalize">{profileData.marital_status || "N/A"}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label>Nationality</Label>
                  {isEditing ? (
                    <Input
                      value={formData.nationality}
                      onChange={(e) => handleInputChange("nationality", e.target.value)}
                    />
                  ) : (
                    <p className="font-medium p-2 bg-muted rounded-md">{profileData.nationality || "N/A"}</p>
                  )}
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label>Address</Label>
                  {isEditing ? (
                    <Textarea
                      value={formData.address}
                      onChange={(e) => handleInputChange("address", e.target.value)}
                    />
                  ) : (
                    <p className="font-medium p-2 bg-muted rounded-md whitespace-pre-wrap">{profileData.address || "N/A"}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Salary Info Tab */}
        <TabsContent value="salary" className="space-y-6">
          {/* Important Note */}
          <Card className="bg-yellow-50/50 border-yellow-200">
            <CardContent className="p-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <p className="font-semibold text-foreground mb-2">Important</p>
                  <div className="text-sm text-muted-foreground space-y-2">
                    <p>
                      The Salary Information tab allows users to define and manage all salary-related details for an employee,
                      including wage type, working schedule, salary components, benefits. Salary components should be calculated
                      automatically based on the defined wage.
                    </p>
                    <div className="space-y-1 mt-3">
                      <p className="font-medium text-foreground">- Wage Type</p>
                      <p className="ml-4">Fixed wage.</p>

                      <p className="font-medium text-foreground mt-2">- Salary Components</p>
                      <p className="ml-4">Section where users can define salary structure components.</p>
                      <p className="ml-4">Each component should include: Basic, House Rent Allowance, Standard Allowance, Performance Bonus, Leave Travel Allowance, Fixed Allowance</p>

                      <p className="ml-4 mt-2">Computation Type: Fixed Amount or Percentage of Wage</p>
                      <p className="ml-4">Value: Percentage field (e.g., 50% for Basic, 50% of Basic for HRA, etc.)</p>

                      <p className="ml-4 mt-2">Salary component values should auto-update when the wage amount changes.</p>
                      <p className="ml-4">The total of all components should not exceed the defined Wage</p>

                      <p className="font-medium text-foreground mt-2">- Automatic Calculation:</p>
                      <p className="ml-4">The system should calculate each component amount based on the employee's defined Wage.</p>
                      <p className="ml-4">Example: If Wage = ₹50,000 and Basic = 50% of wage, then Basic = ₹25,000.</p>
                      <p className="ml-4">If HRA = 50% of Basic, then HRA = ₹12,500.</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Salary Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-6 text-center">
                <p className="text-sm text-muted-foreground mb-2">Month Wage</p>
                {isEditing ? (
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-lg font-bold">₹</span>
                    <Input
                      type="number"
                      value={salaryConfig.monthlyWage}
                      onChange={(e) => handleConfigChange('monthlyWage', e.target.value)}
                      className="w-32 text-center text-lg font-bold"
                    />
                  </div>
                ) : (
                  <p className="text-3xl font-bold text-foreground">₹{Number(salaryConfig.monthlyWage).toLocaleString()}</p>
                )}
                <p className="text-sm text-muted-foreground">/ Month</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6 text-center">
                <p className="text-sm text-muted-foreground mb-2">Yearly Wage</p>
                <p className="text-3xl font-bold text-foreground">₹{(Number(salaryConfig.monthlyWage) * 12).toLocaleString()}</p>
                <p className="text-sm text-muted-foreground">/ Yearly</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6 text-center">
                <p className="text-sm text-muted-foreground mb-2">Working Days</p>
                <p className="text-3xl font-bold text-foreground">{profileData.workingDaysPerWeek}</p>
                <p className="text-sm text-muted-foreground">days/week</p>
              </CardContent>
            </Card>
          </div>

          {/* Salary Components */}
          <Card>
            <CardContent className="p-6 space-y-4">
              <h3 className="text-lg font-semibold">Salary Components</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define Basic salary from company cost compute it based on monthly Wages
              </p>
              <div className="space-y-3">
                {[
                  { key: 'basic_salary', configKey: 'basicPercent', label: 'Basic Salary', desc: 'Basic salary component' },
                  { key: 'hra', configKey: 'hraPercent', label: 'House Rent Allowance', desc: 'HRA provided to employees 50% of the basic salary' },
                  { key: 'standard_allowance', configKey: 'standardAllowancePercent', label: 'Standard Allowance', desc: 'A standard allowance is a predetermined, fixed amount' },
                  { key: 'performance_bonus', configKey: 'performanceBonusPercent', label: 'Performance Bonus', desc: 'Variable amount paid during payroll' },
                  { key: 'lta', configKey: 'ltaPercent', label: 'Leave Travel Allowance', desc: 'LTA is paid by the company to employees to cover their travel expenses' },
                  { key: 'fixed_allowance', configKey: null, label: 'Fixed Allowance', desc: 'Fixed allowance portion of wages' },
                ].map((component) => (
                  <div key={component.key} className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border border-border">
                    <div className="flex-1">
                      <p className="font-medium text-foreground">{component.label}</p>
                      <p className="text-xs text-muted-foreground mt-1">{component.desc}</p>
                    </div>
                    <div className="text-right ml-4 flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-lg font-bold text-foreground">₹{Number(salaryStructure[component.key] || 0).toLocaleString()}</p>
                        <p className="text-sm text-muted-foreground">₹ / month</p>
                      </div>

                      {component.configKey && (
                        <div className="w-24">
                          {isEditing ? (
                            <div className="flex items-center gap-1">
                              <Input
                                type="number"
                                value={salaryConfig[component.configKey as keyof typeof salaryConfig]}
                                onChange={(e) => handleConfigChange(component.configKey!, e.target.value)}
                                className="text-right h-8"
                              />
                              <span className="text-sm text-muted-foreground">%</span>
                            </div>
                          ) : (
                            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                              {Number(salaryConfig[component.configKey as keyof typeof salaryConfig]).toFixed(2)}%
                            </Badge>
                          )}
                        </div>
                      )}
                      {!component.configKey && (
                        <div className="w-24 text-right">
                          <span className="text-sm text-muted-foreground">Balancing</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* PF Contribution & Tax Deductions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* PF Contribution */}
            <Card>
              <CardContent className="p-6 space-y-4">
                <h3 className="text-lg font-semibold">Provident Fund (PF) Contribution</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border border-border">
                    <div>
                      <p className="font-medium text-foreground">Employee</p>
                      <p className="text-xs text-muted-foreground mt-1">PF is calculated based on the basic salary</p>
                    </div>
                    <div className="text-right ml-4 flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-lg font-bold text-foreground">₹{Number(salaryStructure.pf_contribution || 0).toLocaleString()}</p>
                        <p className="text-sm text-muted-foreground">₹ / month</p>
                      </div>
                      <div className="w-24">
                        {isEditing ? (
                          <div className="flex items-center gap-1">
                            <Input
                              type="number"
                              value={salaryConfig.pfPercent}
                              onChange={(e) => handleConfigChange('pfPercent', e.target.value)}
                              className="text-right h-8"
                            />
                            <span className="text-sm text-muted-foreground">%</span>
                          </div>
                        ) : (
                          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                            {Number(salaryConfig.pfPercent).toFixed(2)}%
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tax Deductions */}
            <Card>
              <CardContent className="p-6 space-y-4">
                <h3 className="text-lg font-semibold">Tax Deductions</h3>
                <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border border-border">
                  <div>
                    <p className="font-medium text-foreground">Professional Tax</p>
                    <p className="text-xs text-muted-foreground mt-1">Professional Tax deducted from the Gross salary</p>
                  </div>
                  <div className="text-right">
                    {isEditing ? (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">₹</span>
                        <Input
                          type="number"
                          value={salaryConfig.professionalTax}
                          onChange={(e) => handleConfigChange('professionalTax', e.target.value)}
                          className="w-32 text-right"
                        />
                      </div>
                    ) : (
                      <>
                        <p className="text-lg font-bold text-foreground">₹{Number(salaryStructure.professional_tax || 0).toLocaleString()}</p>
                        <p className="text-sm text-muted-foreground">₹ / month</p>
                      </>
                    )}
                  </div>
                </div>
                <div className="mt-4 p-4 bg-primary/5 rounded-lg border border-primary/20">
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium text-foreground">Break Time:</span> {profileData.breakTime}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
