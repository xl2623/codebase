#!/usr/bin/env python


from tkinter import *  # sarah says bad
from math import *
import numpy as np

class Surface():
    def __init__(self, p1, p2, p3):
        v1 = p3 - p1
        v2 = p2 - p1
        cp = np.cross(v1, v2)
        # coefficient of the function of the plane
        self.a = cp[0] 
        self.b = cp[1]
        self.c = cp[2]
        self.d = np.dot(cp, p3)
        # angle with respect to z axis
        self.angle = atan(sqrt(cp[0]**2+cp[1]**2)/cp[2])
        self.color = self.angle2color()

        self.p0xy = p1[0:2]
        self.p1xy = p2[0:2]
        self.p2xy = p3[0:2]
    
    def getz(self, point):
        if (self.ifon(point)):
            return -(self.d - self.a*point[0] - self.b*point[1])/self.c
        else:
            return float("-inf")

    def getcolor(self):
        return self.color

    def getangle(self):
        return self.angle

    def angle2color(self):
        #return int(-510/pi*abs(self.angle)+255)
        return int(-320/pi*abs(self.angle)+255)

    # check if on the surface
    def ifon(self, p_test):       
        dX = p_test[0] - self.p0xy[0]
        dY = p_test[1] - self.p0xy[1]
        dX20 = self.p2xy[0] - self.p0xy[0]
        dY20 = self.p2xy[1] - self.p0xy[1]
        dX10 = self.p1xy[0] - self.p0xy[0]
        dY10 = self.p1xy[1] - self.p0xy[1]

        s_p = (dY20*dX) - (dX20*dY)
        t_p = (dX10*dY) - (dY10*dX)
        D = (dX10*dY20) - (dY10*dX20)

        if D > 0:
            return ((s_p >= 0) and (t_p >= 0) and (s_p + t_p) <= D)
        else:
            return ((s_p <= 0) and (t_p <= 0) and (s_p + t_p) >= D)

    # check if x y is with in the boundry of this surface

class Obj():
    '''                 Type                                 Des
    self.nv             int                                  # of vertices
    self.nf             int                                  # of faces
    self.ne             int                                  # of edges
    self.vertices       3xself.nv ndarray                    (x,y,z)^T location of each vertex as each col
    self.faces          list with 3x1 ndarray element        (id1, id2, id3)^T index of the three vertices that forms the face
    self.edges          list with list as element            the vertices current vertex connects to
    self.orientation    3x3 ndarray each col is orthnormal   orientation of the object represented as a rotation matrix
    '''
    def __init__(self, filename):
        # open and close file
        # read the entire file as a string
        file = open(filename, "r")
        param_str = file.read()
        file.close()

        # process the param_str
        # to form a 2D list, first dimension is line
        #                    second dimension is numbers on the line
        param_list_init = param_str.split("\n")      
        param_list_final = []
        for i in range(0,len(param_list_init)):
            param_list_final.append(param_list_init[i].split(",")) 
            
        # assign values to class attributes
        self.nv = int(param_list_final[0][0])    # number of vertices
        self.nf = int(param_list_final[0][1])    # number of faces
        
        # extract all the vertices positions
        self.vertices = np.zeros([4, self.nv])
        for i in range(1, self.nv+1):
            self.vertices[0,i-1] = float(param_list_final[i][0])
            self.vertices[1,i-1] = float(param_list_final[i][1])
            self.vertices[2,i-1] = float(param_list_final[i][2])
            self.vertices[3,i-1] = float(param_list_final[i][3])
        self.vertices = self.vertices[:,np.argsort(self.vertices[0, :])]
        self.vertices = np.delete(self.vertices, 0, 0)
        # self.vertices is a 3 by self.nv matrix in the order of index

        # extract all the face indices
        self.faces = []
        for i in range(1+self.nv, 1+self.nv+self.nf):
            self.faces.append(np.array([int(param_list_final[i][0])-1, int(param_list_final[i][1])-1, int(param_list_final[i][2])-1]))
        # self.faces is a list with each element as a 3 by 1 vector, each element of the vector denotes the index of vertices

        # compute edge information
        self.edges = []
        # find which vertex is connected to which vertices
        for j in range(0,self.nv):
            temp = []
            for i in range(0, self.nf):
                if (self.faces[i][0]==j) or (self.faces[i][1]==j) or (self.faces[i][2]==j):
                    for k in range(0,3):
                        if (self.faces[i][k]!=j):
                            temp.append(self.faces[i][k])
            # remove redundant vertices
            temp_unique = []                
            [temp_unique.append(x) for x in temp if x not in temp_unique]
            self.edges.append(temp_unique)
        # remove two way connections
        norepeat_unique_edges = [] 
        norepeat_unique_edges.append(self.edges[0])
        for i in range(1, len(self.edges)):
            toappend = self.edges[i].copy()
            for j in range(len(self.edges[i])):
                for k in range(0,i):
                    if self.edges[i][j] == k:
                        toappend.remove(k)
            norepeat_unique_edges.append(toappend)
        self.edges = norepeat_unique_edges
        
        self.ne = 0
        # compute number of edges
        for element in self.edges:
            self.ne += len(element) 

        # set initial orientation of the obj to be identity
        self.orientation = np.eye(3)

        # compute average edge distance
        # for scaling
        sum = 0
        for i in range(len(self.edges)):
            for j in range(len(self.edges[i])):
                sum += sqrt((self.vertices[0, i]-self.vertices[0, self.edges[i][j]])**2+(self.vertices[1, i]-self.vertices[1, self.edges[i][j]])**2)
        average = sum/self.ne
        self.scale = 60/average

        # create a dummy image
        self.img = PhotoImage(width=640, height=480)

        # create surface objects for each surface
        lines = self.get_lines()
        self.surfaces = []
        # lines is of dimension self.nf by 1
        # each element of lines is a ndarray
        # each ndarray is 3x3
        # each col of the ndarray describe one of the vertex defining the surface
        for i in range(len(lines)):
            vec1 = lines[i][:, 0]
            vec2 = lines[i][:, 1]
            vec3 = lines[i][:, 2]
            self.surfaces.append(Surface(vec1, vec2, vec3))

        # bounding box of the figure
        self.minx = 0.0
        self.miny = 0.0
        self.maxx = 0.0
        self.maxy = 0.0

    def rotate_world(self, R_matrix):
        # takes in a rotation matrix describing the orientation of the obj wrt the world 
        # updates the orientation of all the vertices of the obj
        self.orientation = R_matrix
        self.vertices = self.orientation @ self.vertices

    def get_lines(self):
        # get lines connecting all the vertices
        lines = []
        for i in range(0, self.nf):
            lines.append(self.vertices[:,self.faces[i]])
        return lines

    def find_min_max(self):
        self.maxx = np.max(self.vertices[0,:])
        self.maxy = np.max(self.vertices[1,:])
        self.minx = np.min(self.vertices[0,:])
        self.miny = np.min(self.vertices[1,:])

    def rgb(self, r, g, b):
        return "#%s%s%s" % tuple([hex(c)[2:].rjust(2, "0")
            for c in (r, g, b)])


    def drawobj(self, canvas, color, widthx, widthy):
        self.minx = 0.0
        self.miny = 0.0
        self.maxx = 0.0
        self.maxy = 0.0
        # draw the object
        w = widthx/2
        h = widthy/2
        myWidth = widthx
        myHeight = widthy
        canvas.delete(ALL) # delete all edges
        # we first scale the object to a visiable size
        lines = self.get_lines()
        self.surfaces = []
        for i in range(len(lines)):
            vec1 = lines[i][:, 0]
            vec2 = lines[i][:, 1]
            vec3 = lines[i][:, 2]
            self.surfaces.append(Surface(vec1, vec2, vec3))

        canvas.pack()
        # print(myWidth)
        # print(myHeight)
        self.img = PhotoImage(width=myWidth, height=myHeight)
        canvas.create_image((myWidth/2, myHeight/2), image=self.img, state="normal")
        
        self.find_min_max()
        #print(self.maxx)
        #print(self.maxy)
        #print(self.minx)
        #print(self.miny)
        #use this to do pixel level manipulation
        #shot gun the entire plane to check for visible surface
        for x in range(int(self.minx*self.scale), int(self.maxx*self.scale)):
            for y in range(int(self.miny*self.scale), int(self.maxy*self.scale)):
                maxz = [float("-inf"), -1]
                zdebug = []
                for index in range(self.nf):
                    #print(str(index),zdebug)
                    #print(maxz)
                    if self.surfaces[index].getz(np.array([x/self.scale, y/self.scale])) > float("-inf"):
                        zdebug.append(self.surfaces[index].getz(np.array([x/self.scale, y/self.scale])))
                        if self.surfaces[index].getz(np.array([x/self.scale, y/self.scale])) > maxz[0]:
                            maxz[0] = self.surfaces[index].getz(np.array([x/self.scale, y/self.scale]))
                            maxz[1] = index
                            #print(maxz[0])

                # goal: find a surface that's visible
                # use the assign index 
                if maxz[1] != -1:
                    #self.img.put(self.rgb_to_hex((0, 0, self.surfaces[index].getcolor())), ())
                    canvas.create_rectangle(int(x+w-1),int(h-y-1), int(x+w+1),int(h-y+1), fill = self.rgb(0, 0, self.surfaces[maxz[1]].getcolor()), outline=self.rgb(0, 0, self.surfaces[maxz[1]].getcolor()))
        # create lines between vertices
        # for i in range(len(self.edges)):
        #     for j in range(len(self.edges[i])):
        #         canvas.create_line(self.vertices[0, i]*self.scale+w, -self.vertices[1, i]*self.scale+h,
        #                            self.vertices[0, self.edges[i][j]]*self.scale+w, -self.vertices[1, self.edges[i][j]]*self.scale+h, fill = color)
        
        # draw x y axis
        # canvas.create_line(0.0+w, 0.0+h, 0.0+w, -self.scale+h, fill = "red", arrow='last', arrowshape='20 40 10')
        # canvas.create_line(0.0+w, 0.0+h, self.scale+w, 0.0+h, fill = "red", arrow='last', arrowshape='20 40 10')

        # draw points on each vertex
        # for i in range(self.vertices.shape[1]):
        #     canvas.create_oval(self.scale*(self.vertices[0,i]-0.05)+w, -self.scale*(self.vertices[1,i]-0.05)+h, 
        #                        self.scale*(self.vertices[0,i]+0.05)+w, -self.scale*(self.vertices[1,i]+0.05)+h, fill=color)
        
        # canvas.pack()
        # width = 100
        # height = 100
        # import pdb;pdb.set_trace()


    # useless
    def colordrawobj(self, canvas, color, widthx, widthy):
        # draw the object
        w = widthx/2
        h = widthy/2

        canvas.delete(ALL) # delete all edges
        # we first scale the object to a visiable size


        for i in range(len(self.edges)):
            for j in range(len(self.edges[i])):
                canvas.create_line(self.vertices[0, i]*self.scale+w, -self.vertices[1, i]*self.scale+h,
                                   self.vertices[0, self.edges[i][j]]*self.scale+w, -self.vertices[1, self.edges[i][j]]*self.scale+h, fill = color)
        
        # draw x y axis
        canvas.create_line(0.0+w, 0.0+h, 0.0+w, -self.scale+h, fill = "red", arrow='last', arrowshape='20 40 10')
        canvas.create_line(0.0+w, 0.0+h, self.scale+w, 0.0+h, fill = "red", arrow='last', arrowshape='20 40 10')

        # draw points on each vertex
        for i in range(self.vertices.shape[1]):
            canvas.create_oval(self.scale*(self.vertices[0,i]-0.05)+w, -self.scale*(self.vertices[1,i]-0.05)+h, 
                               self.scale*(self.vertices[0,i]+0.05)+w, -self.scale*(self.vertices[1,i]+0.05)+h, fill=color)

    # currently useless
    # consider move the comments to Surface class
    def get_normal(self):
        lines = self.get_lines()
        # print(lines)
        # lines is of dimension self.nf by 1
        # each element of lines is a ndarray
        # each ndarray is 3x3
        # each col of the ndarray describe one of the vertex defining the surface
        angles = []
        for i in range(len(lines)):
            # for each ndarray, consider the coordinate frame defined on the first point
            # with identity orientation
            # subtract the second point and third point from the first point
            # this gives the vector point from the first point to the second and third point
            # cross product is performed
            vec1 = np.zeros([3, 1])
            vec2 = np.zeros([3, 1])
            # normal = np.zeros([3, 1])
            vec1 = -(lines[i][:, 0]-lines[i][:, 1])
            vec2 = -(lines[i][:, 0]-lines[i][:, 2])
            normal = np.cross(vec1, vec2)
            
            # for each normal, the angle it makes with repspect to z is
            # arctan(sqrt(x^2+y^2)/z)
            # found angle in radian
            angles.append(atan(sqrt(normal[0]**2+normal[1]**2)/normal[2]))

        colors = self.angle2color(angles)

        #print(angles)
        #print(colors)
        return None

    def angle2color(self, angles):
        colors = []
        for angle in angles:
            colors.append(int((225-95)/(pi/2)*angle+95))
        return colors

class Graphics():
    def __init__(self, filename):
        self.root = Tk()
        self.root.title('Viewer')
        self.root.geometry('+100+100')
        self.bgColor = 'white'
        self.widthx = 500
        self.widthy = 500
        self.canvas = Canvas(self.root, width=self.widthx, height=self.widthy, background=self.bgColor)
        self.prevX = 0.0
        self.prevY = 0.0
        self.canvas.pack(fill=BOTH,expand=YES)               
        self.canvas.bind("<Button-1>", self.leftclick)
        self.canvas.bind("<B1-Motion>", self.mousemotion)
        self.canvas.bind("<Configure>", self.resize)

        self.objcolor = 'blue'
        self.object3D = Obj(filename)
        self.object3D.get_normal()
        # print(object3D.get_lines())

    def run(self):
        self.object3D.drawobj(self.canvas, self.objcolor, self.widthx, self.widthy)


    def resize(self, event):
        print("I'm in call back")
        self.object3D.drawobj(self.canvas, self.objcolor, self.widthx, self.widthy)
        
    def leftclick(self, event):
        self.prevX = event.x
        self.prevY = event.y

    def mousemotion(self, event):
        currX = event.x
        currY = event.y
        dx = currX - self.prevX
        dy = currY - self.prevY
        self.rotate(dx, dy)
        #self.prevX = currX
        #self.prevY = currY
        self.leftclick(event)

    def rotate(self, dx, dy):
        alphay = (dx)*pi/180
        alphax = (dy)*pi/180
        xrotation = np.array([[1.0,     0.0,            0.0],
                              [0.0,     cos(alphax),    -sin(alphax)],
                              [0.0,     sin(alphax),    cos(alphax)]]) # rotation about x
        yrotation = np.array([[cos(alphay),     0.0,    sin(alphay)],
                              [0.0,             1.0,    0.0],
                              [-sin(alphay),    0.0,    cos(alphay)]]) # rotation about y
        combined_rotation = xrotation @ yrotation
        self.object3D.rotate_world(combined_rotation)
        self.object3D.drawobj(self.canvas, self.objcolor, self.widthx, self.widthy)
   
def main():

    G = Graphics("object.txt")
    G.run()
    
    mainloop()

if __name__=='__main__':
    sys.exit(main())

    