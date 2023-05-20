import numpy as np
import cv2
import time
import json


# print("Thông số ban đầu của máy đo:")
# min_angle = input('Góc tối thiểu (góc quay số thấp nhất có thể) - tính bằng độ: ')
# max_angle = input('Góc tối đa (góc cao nhất có thể) - tính bằng độ: ')
# min_value = input('Giá trị nhỏ nhất của đồng hồ: ') # 0
# max_value = input('Giá trị lớn nhất của đồng hồ: ') # 150
# units = input('Đơn vị đo: ') #đơn vị đo của đồng hồ

min_angle = 40
max_angle = 305
min_value = 0
max_value = 150
units = 'psi'
cap = cv2.VideoCapture("./video/1.mp4")
#cap = cv2.VideoCapture(0)



#Chương trình ghi dữ liệu đồng hồ vào trong file Json
def writedataTojson(path, filename, data):
	filepathdata = './' + path + '/' + filename + '.json'
	with open(filepathdata, 'w') as fp:
		json.dump(data, fp)


path = './dataJson'
filename = 'data'

data = {}


#chương trình tạo vòng tròn trung bình
def avg_circles(circles, b):
    avg_x=0
    avg_y=0
    avg_r=0
    for i in range(b):
        avg_x = avg_x + circles[0][i][0]
        avg_y = avg_y + circles[0][i][1]
        avg_r = avg_r + circles[0][i][2]
    avg_x = int(avg_x/(b))
    avg_y = int(avg_y/(b))
    avg_r = int(avg_r/(b))
    return avg_x, avg_y, avg_r




def dist_2_pts(x1, y1, x2, y2):
	return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
	
while(cap.isOpened()): 
	while True:
		try:

			#mở camera
			ret, img = cap.read()
			#cv2.imshow('DONG HO AP', img)

			#Chuong trinh hieu chinh
			img_blur = cv2.GaussianBlur(img, (5,5), 3) # hàm làm mờ ảnh bằng bộ lọc GaussianBlur
			gray = cv2.cvtColor(img_blur, cv2.COLOR_BGR2GRAY)  #chuyển ảnh màu sang ảnh xám
			height, width = img.shape[:2] #lấy chiều cao và chiều rộng của ảnh
			
			#Nhận diện vòng tròn trong ảnh với phương phương pháp HoughCircles của thư viện OPENCV
			circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, np.array([]), 100, 50, int(height*0.35), int(height*0.48))
			a, b, c = circles.shape
			x,y,r = avg_circles(circles, b)

			#Vẽ tâm và hình tròn bao quanh đồng hồ áp
			cv2.circle(img, (x, y), r, (0, 0, 255), 3, cv2.LINE_AA)  # Vẽ vòng tròn
			cv2.circle(img, (x, y), 2, (0, 255, 0), 3, cv2.LINE_AA)  # Vẽ tâm
			#cv2.imshow("hinh anh ve", img)

			separation = 10.0 #Tăng 10 đơn vị cho mỗi bước ví dụ: 10, 20, 30... 360
			interval = int(360 / separation)
			p1 = np.zeros((interval,2)) 
			p2 = np.zeros((interval,2))
			p_text = np.zeros((interval,2))
			for i in range(0,interval):
				for j in range(0,2):
					if (j%2==0):
						p1[i][j] = x + 0.9 * r * np.cos(separation * i * 3.14 / 180) 
					else:
						p1[i][j] = y + 0.9 * r * np.sin(separation * i * 3.14 / 180)
			text_offset_x = 10
			text_offset_y = 5
			for i in range(0, interval):
				for j in range(0, 2):
					if (j % 2 == 0):
						p2[i][j] = x + r * np.cos(separation * i * 3.14 / 180)
						p_text[i][j] = x - text_offset_x + 1.2 * r * np.cos((separation) * (i+9) * 3.14 / 180) # tính toán hiển thị góc - số quanh đồng hồ
					else:
						p2[i][j] = y + r * np.sin(separation * i * 3.14 / 180)
						p_text[i][j] = y + text_offset_y + 1.2* r * np.sin((separation) * (i+9) * 3.14 / 180)  

			#Thêm các dòng và chữ lên ảnh
			for i in range(0,interval):
				cv2.line(img, (int(p1[i][0]), int(p1[i][1])), (int(p2[i][0]), int(p2[i][1])),(0, 255, 0), 2)
				cv2.putText(img, '%s' %(int(i*separation)), (int(p_text[i][0]), int(p_text[i][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.3,(0,0,0),1,cv2.LINE_AA)
			
			cv2.imshow("hinh anh ve so", img)

			#chuyển hình ảnh hiện tại sang ảnh xám để tìm đường giá trị của kim trong đồng hồ
			gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			thresh = 175
			maxValue = 255
			th, dst2 = cv2.threshold(gray2, thresh, maxValue, cv2.THRESH_BINARY_INV)
			minLineLength = 10
			maxLineGap = 0
			lines = cv2.HoughLinesP(image=dst2, rho=3, theta=np.pi / 180, threshold=100,minLineLength=minLineLength, maxLineGap=0)  # rho is set to 3 to detect more lines, easier to get more then filter them out later

			# remove all lines outside a given radius
			final_line_list = []
			#print "radius: %s" %r

			diff1LowerBound = 0.15 #diff1LowerBound and diff1UpperBound determine how close the line should be from the center
			diff1UpperBound = 0.25
			diff2LowerBound = 0.5 #diff2LowerBound and diff2UpperBound determine how close the other point of the line should be to the outside of the gauge
			diff2UpperBound = 1.0
			for i in range(0, len(lines)):
				for x1, y1, x2, y2 in lines[i]:
					diff1 = dist_2_pts(x, y, x1, y1)  # x, y is center of circle
					diff2 = dist_2_pts(x, y, x2, y2)  # x, y is center of circle
					#đặt diff1 thành giá trị nhỏ hơn (gần tâm nhất) của hai giá trị), giúp việc tính toán trở nên dễ dàng hơn
					if (diff1 > diff2):
						temp = diff1
						diff1 = diff2
						diff2 = temp
					# kiểm tra xem dòng có nằm trong phạm vi chấp nhận được không
					if (((diff1<diff1UpperBound*r) and (diff1>diff1LowerBound*r) and (diff2<diff2UpperBound*r)) and (diff2>diff2LowerBound*r)):
						line_length = dist_2_pts(x1, y1, x2, y2)
						final_line_list.append([x1, y1, x2, y2])

			# assumes the first line is the best one
			x1 = final_line_list[0][0]
			y1 = final_line_list[0][1]
			x2 = final_line_list[0][2]
			y2 = final_line_list[0][3]
			cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

			
			#tìm điểm xa tâm nhất dùng để xác định góc
			dist_pt_0 = dist_2_pts(x, y, x1, y1)
			dist_pt_1 = dist_2_pts(x, y, x2, y2)
			if (dist_pt_0 > dist_pt_1):
				x_angle = x1 - x
				y_angle = y - y1
			else:
				x_angle = x2 - x
				y_angle = y - y2
			# take the arc tan of y/x to find the angle
			res = np.arctan(np.divide(float(y_angle), float(x_angle)))
			

			#chúng được xác định bằng thử và sai
			res = np.rad2deg(res)
			if x_angle > 0 and y_angle > 0:  #Góc phần tư 1
				final_angle = 270 - res
			if x_angle < 0 and y_angle > 0:  #Góc phần tư 2
				final_angle = 90 - res
			if x_angle < 0 and y_angle < 0:  #Góc phần tư 3
				final_angle = 90 - res
			if x_angle > 0 and y_angle < 0:  #Góc phần tư 4
				final_angle = 270 - res


# Công thức này là công thức chuyển đổi giá trị từ một phạm vi (range) giá trị cũ sang một phạm vi giá trị mới.

# Cụ thể, công thức này sử dụng các giá trị sau đây:

# old_value: giá trị cũ cần được chuyển đổi sang phạm vi giá trị mới
# old_min: giá trị nhỏ nhất của phạm vi giá trị cũ
# old_range: phạm vi giá trị cũ (chênh lệch giữa giá trị lớn nhất và giá trị nhỏ nhất của phạm vi giá trị cũ)
# new_min: giá trị nhỏ nhất của phạm vi giá trị mới
# new_range: phạm vi giá trị mới (chênh lệch giữa giá trị lớn nhất và giá trị nhỏ nhất của phạm vi giá trị mới)
# new_value: giá trị sau khi chuyển đổi sang phạm vi giá trị mới

# Công thức này sẽ tính toán giá trị mới bằng cách lấy giá trị cũ trừ đi giá trị nhỏ nhất của phạm vi cũ, sau đó nhân với phạm vi giá trị mới và chia cho phạm vi giá trị cũ. Kết quả sẽ được cộng với giá trị nhỏ nhất của phạm vi giá trị mới để tính ra giá trị mới chuyển đổi.
			

			old_min = float(min_angle)
			old_max = float(max_angle)

			new_min = float(min_value)
			new_max = float(max_value)

			old_value = final_angle

			old_range = (old_max - old_min)
			new_range = (new_max - new_min)
			new_value = (((old_value - old_min) * new_range) / old_range) + new_min
			
			val = new_value
			#========================

			print ("Gia tri: %s %s" %(("%.2f" % val), units))
			data['donghoap'] = val
			writedataTojson(path, filename, data) #thực hiện quá trình ghi dữ liệu giá trị đồng hồ hiện tại vào file Json
		
			if cv2.waitKey(30) & 0xff == ord('q'):
				break
				
		except ValueError as ve:
			x = "do nothing"
		except IndexError:
			x = "do nothing"
			
	cap.release()
	cv2.destroyAllWindows()
else:
	print("Cảnh báo - Mất kết nối với camera !")