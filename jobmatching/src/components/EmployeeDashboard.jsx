import React, { useState, useEffect } from 'react';
import { LineChart,Line, BarChart, PieChart, Cell, Bar, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { parse } from 'papaparse';

// Dashboard component
export default function EmployeeDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [file, setFile] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  
  // Colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#8dd1e1'];
  
  // Handle file upload
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    setFile(file);
    
    // Parse the CSV file
    const reader = new FileReader();
    reader.onload = async ({ target }) => {
      try {
        const csv = target.result;
        const parsedData = parse(csv, {
          header: true,
          skipEmptyLines: true,
          dynamicTyping: true,
        });
        
        // Process the data
        const processedData = processData(parsedData.data);
        setData(processedData);
        setLoading(false);
      } catch (err) {
        setError("Error processing the file. Please check the format.");
        setLoading(false);
      }
    };
    
    reader.onerror = () => {
      setError("Error reading the file");
      setLoading(false);
    };
    
    reader.readAsText(file);
  };
  
  // Process the data for visualization
  const processData = (rawData) => {
    // Basic statistics
    const processedData = {
      totalEmployees: rawData.length,
      demographics: {},
      salary: {},
      experience: {},
      education: {},
      skills: {},
      departments: {},
    };
    
    // Gender distribution
    const genderCount = {};
    rawData.forEach(emp => {
      if (emp.gender) {
        genderCount[emp.gender] = (genderCount[emp.gender] || 0) + 1;
      }
    });
    processedData.demographics.gender = Object.keys(genderCount).map(g => ({
      name: g,
      value: genderCount[g]
    }));
    
    // Department distribution
    const deptCount = {};
    rawData.forEach(emp => {
      if (emp.department) {
        deptCount[emp.department] = (deptCount[emp.department] || 0) + 1;
      }
    });
    processedData.departments.distribution = Object.keys(deptCount).map(d => ({
      name: d,
      value: deptCount[d]
    }));
    
    // Education level distribution
    const eduCount = {};
    rawData.forEach(emp => {
      if (emp.highest_education) {
        eduCount[emp.highest_education] = (eduCount[emp.highest_education] || 0) + 1;
      }
    });
    processedData.education.distribution = Object.keys(eduCount).map(e => ({
      name: e,
      value: eduCount[e]
    }));
    
    // Years of experience distribution
    const expGroups = {
      '0-2 years': 0,
      '3-5 years': 0,
      '6-10 years': 0,
      '11-15 years': 0,
      '16-20 years': 0,
      '20+ years': 0
    };
    
    rawData.forEach(emp => {
      if (emp.years_experience !== undefined && emp.years_experience !== null) {
        const yrs = emp.years_experience;
        if (yrs <= 2) expGroups['0-2 years']++;
        else if (yrs <= 5) expGroups['3-5 years']++;
        else if (yrs <= 10) expGroups['6-10 years']++;
        else if (yrs <= 15) expGroups['11-15 years']++;
        else if (yrs <= 20) expGroups['16-20 years']++;
        else expGroups['20+ years']++;
      }
    });
    
    processedData.experience.distribution = Object.keys(expGroups).map(e => ({
      name: e,
      value: expGroups[e]
    }));
    
    // Salary distribution by department
    const salaryByDept = {};
    rawData.forEach(emp => {
      if (emp.department && emp.salary) {
        if (!salaryByDept[emp.department]) {
          salaryByDept[emp.department] = {
            total: 0,
            count: 0
          };
        }
        salaryByDept[emp.department].total += emp.salary;
        salaryByDept[emp.department].count += 1;
      }
    });
    
    processedData.salary.byDepartment = Object.keys(salaryByDept).map(d => ({
      name: d,
      value: salaryByDept[d].total / salaryByDept[d].count
    }));
    
    // Salary distribution by experience
    const salaryByExp = [
      { name: '0-2 years', avg: 0, count: 0 },
      { name: '3-5 years', avg: 0, count: 0 },
      { name: '6-10 years', avg: 0, count: 0 },
      { name: '11-15 years', avg: 0, count: 0 }, 
      { name: '16-20 years', avg: 0, count: 0 },
      { name: '20+ years', avg: 0, count: 0 }
    ];
    
    rawData.forEach(emp => {
      if (emp.years_experience !== undefined && emp.salary) {
        const yrs = emp.years_experience;
        let index = 0;
        if (yrs <= 2) index = 0;
        else if (yrs <= 5) index = 1;
        else if (yrs <= 10) index = 2;
        else if (yrs <= 15) index = 3;
        else if (yrs <= 20) index = 4;
        else index = 5;
        
        salaryByExp[index].avg += emp.salary;
        salaryByExp[index].count += 1;
      }
    });
    
    // Calculate average
    salaryByExp.forEach(item => {
      if (item.count > 0) {
        item.value = item.avg / item.count;
        delete item.avg;
        delete item.count;
      } else {
        item.value = 0;
      }
    });
    
    processedData.salary.byExperience = salaryByExp;
    
    // Technical skills analysis
    const skillsCount = {};
    rawData.forEach(emp => {
      if (emp.technical_skills) {
        // Handle skills as comma-separated values
        const skills = typeof emp.technical_skills === 'string' 
          ? emp.technical_skills.split(',').map(s => s.trim())
          : [emp.technical_skills];
          
        skills.forEach(skill => {
          if (skill) {
            skillsCount[skill] = (skillsCount[skill] || 0) + 1;
          }
        });
      }
    });
    
    // Sort skills by frequency and take top 10
    const topSkills = Object.keys(skillsCount)
      .map(skill => ({ name: skill, value: skillsCount[skill] }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);
    
    processedData.skills.top = topSkills;
    
    return processedData;
  };
  
  // Sample data for initial display when no file is uploaded
  useEffect(() => {
    if (!file) {
      const sampleData = {
        totalEmployees: 250,
        demographics: {
          gender: [
            { name: 'Male', value: 140 },
            { name: 'Female', value: 110 }
          ]
        },
        departments: {
          distribution: [
            { name: 'Engineering', value: 80 },
            { name: 'Marketing', value: 50 },
            { name: 'HR', value: 30 },
            { name: 'Finance', value: 40 },
            { name: 'Sales', value: 50 }
          ]
        },
        education: {
          distribution: [
            { name: 'Bachelor', value: 120 },
            { name: 'Master', value: 80 },
            { name: 'PhD', value: 30 },
            { name: 'High School', value: 20 }
          ]
        },
        experience: {
          distribution: [
            { name: '0-2 years', value: 40 },
            { name: '3-5 years', value: 70 },
            { name: '6-10 years', value: 60 },
            { name: '11-15 years', value: 45 },
            { name: '16-20 years', value: 25 },
            { name: '20+ years', value: 10 }
          ]
        },
        salary: {
          byDepartment: [
            { name: 'Engineering', value: 85000 },
            { name: 'Marketing', value: 65000 },
            { name: 'HR', value: 55000 },
            { name: 'Finance', value: 75000 },
            { name: 'Sales', value: 60000 }
          ],
          byExperience: [
            { name: '0-2 years', value: 50000 },
            { name: '3-5 years', value: 65000 },
            { name: '6-10 years', value: 80000 },
            { name: '11-15 years', value: 95000 },
            { name: '16-20 years', value: 110000 },
            { name: '20+ years', value: 130000 }
          ]
        },
        skills: {
          top: [
            { name: 'JavaScript', value: 50 },
            { name: 'Python', value: 45 },
            { name: 'SQL', value: 40 },
            { name: 'Java', value: 35 },
            { name: 'Marketing', value: 30 },
            { name: 'Data Analysis', value: 25 },
            { name: 'Project Management', value: 20 },
            { name: 'Excel', value: 15 },
            { name: 'Communication', value: 10 },
            { name: 'Leadership', value: 5 }
          ]
        }
      };
      
      setData(sampleData);
      setLoading(false);
    }
  }, [file]);
  
  // Tab data
  const tabs = [
    { id: 0, label: 'Demographics' },
    { id: 1, label: 'Departments' },
    { id: 2, label: 'Education & Experience' },
    { id: 3, label: 'Salary Analysis' },
    { id: 4, label: 'Skills' }
  ];
  
  // Custom tab rendering
  const renderTabContent = () => {
    switch (activeTab) {
      case 0:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-4">Gender Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data?.demographics?.gender || []}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {data?.demographics?.gender?.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div>
              <h3 className="text-xl font-semibold mb-4">Demographics Insights</h3>
              <div className="bg-gray-50 p-4 rounded-lg h-64 overflow-y-auto">
                <p className="mb-2">Total employees: <span className="font-semibold">{data?.totalEmployees}</span></p>
                {data?.demographics?.gender?.map((gender, idx) => (
                  <p key={idx} className="mb-2">
                    {gender.name}: <span className="font-semibold">{gender.value}</span> employees 
                    ({((gender.value / data.totalEmployees) * 100).toFixed(1)}%)
                  </p>
                ))}
                <p className="mt-4 text-gray-700">
                  Demographics information helps in understanding the workforce composition and can be useful for diversity initiatives and targeted training programs.
                </p>
              </div>
            </div>
          </div>
        );
      case 1:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-4">Department Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data?.departments?.distribution || []}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#8884d8" name="Employees" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div>
              <h3 className="text-xl font-semibold mb-4">Department Insights</h3>
              <div className="bg-gray-50 p-4 rounded-lg h-64 overflow-y-auto">
                {data?.departments?.distribution?.map((dept, idx) => (
                  <p key={idx} className="mb-2">
                    {dept.name}: <span className="font-semibold">{dept.value}</span> employees 
                    ({((dept.value / data.totalEmployees) * 100).toFixed(1)}%)
                  </p>
                ))}
                <p className="mt-4 text-gray-700">
                  Department distribution provides insights into organizational structure and can be useful for resource allocation and job matching strategies.
                </p>
              </div>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-4">Education Level Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data?.education?.distribution || []}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {data?.education?.distribution?.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div>
              <h3 className="text-xl font-semibold mb-4">Experience Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data?.experience?.distribution || []}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#82ca9d" name="Employees" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-4">Average Salary by Department</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data?.salary?.byDepartment || []}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                    <Legend />
                    <Bar dataKey="value" fill="#8884d8" name="Average Salary" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div>
              <h3 className="text-xl font-semibold mb-4">Salary by Experience</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={data?.salary?.byExperience || []}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                    <Legend />
                    <Line type="monotone" dataKey="value" stroke="#ff7300" name="Average Salary" activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-4">Top 10 Technical Skills</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data?.skills?.top || []}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={100} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#8884d8" name="Employees" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div>
              <h3 className="text-xl font-semibold mb-4">Skills Insights</h3>
              <div className="bg-gray-50 p-4 rounded-lg h-64 overflow-y-auto">
                <p className="mb-4">Most common skills across the organization:</p>
                {data?.skills?.top?.map((skill, idx) => (
                  <p key={idx} className="mb-2">
                    {idx + 1}. {skill.name}: <span className="font-semibold">{skill.value}</span> employees 
                    ({((skill.value / data.totalEmployees) * 100).toFixed(1)}%)
                  </p>
                ))}
                <p className="mt-4 text-gray-700">
                  Skills analysis can help identify training needs and assist with job matching by aligning employee skills with department requirements.
                </p>
              </div>
            </div>
          </div>
        );
      default:
        return <div>Select a tab to view data</div>;
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading data...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-500">{error}</div>
      </div>
    );
  }
  
  return (
    <div className="p-4 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-center">Employee Data Analysis Dashboard</h1>
      
      {/* File upload */}
      <div className="mb-8 p-4 border rounded-lg bg-gray-50 text-center">
        <h2 className="text-xl mb-4">Upload Employee Data</h2>
        <input 
          type="file" 
          accept=".csv" 
          onChange={handleFileUpload}
          className="block w-full text-sm text-gray-500
                     file:mr-4 file:py-2 file:px-4
                     file:rounded-full file:border-0
                     file:text-sm file:font-semibold
                     file:bg-blue-50 file:text-blue-700
                     hover:file:bg-blue-100"
        />
        {file && <div className="mt-2 text-sm text-gray-600">Loaded file: {file.name}</div>}
        {!file && <div className="mt-2 text-sm text-gray-600">Sample data is being shown. Upload your CSV to see actual results.</div>}
      </div>
      
      {/* Summary stats */}
      <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Total Employees</h3>
          <p className="text-3xl font-bold">{data?.totalEmployees || 0}</p>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Departments</h3>
          <p className="text-3xl font-bold">{data?.departments?.distribution?.length || 0}</p>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Education Levels</h3>
          <p className="text-3xl font-bold">{data?.education?.distribution?.length || 0}</p>
        </div>
      </div>
      
      {/* Custom tabs implementation */}
      <div className="mb-8">
        <div className="flex mb-4 border-b">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`p-2 cursor-pointer ${activeTab === tab.id ? 'border-b-2 border-blue-500 font-semibold' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        
        <div className="py-4">
          {renderTabContent()}
        </div>
      </div>
      
      {/* Job Matching Recommendations */}
      <div className="mt-8 p-4 border rounded-lg bg-blue-50">
        <h2 className="text-xl font-semibold mb-4">Job Matching Recommendations</h2>
        <p className="mb-4">Based on the data analysis, consider the following for optimal job matching:</p>
        <ul className="list-disc pl-5 space-y-2">
          <li>Match employees with departments that align with their technical skills profile</li>
          <li>Consider experience levels when matching to roles with specific seniority requirements</li>
          <li>Use education background as a secondary matching criterion after skills and experience</li>
          <li>For roles requiring diverse skill sets, prioritize candidates with multiple complementary skills</li>
        </ul>
        <p className="mt-4 text-sm text-gray-600">For more detailed recommendations, upload your specific data and constraints.</p>
      </div>
    </div>
  );
}