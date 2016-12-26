clear;
%%% open udp
echoudp('on',4012);
u=udp('127.0.0.1', 4012, 'LocalPort', 4950);
fopen(u);

% control loop
zeroflag=0;
Mz=eye(3,3);
while(1)
    A = str2num(fscanf(u));
%     x=A(2);y=A(3);z=A(4);w=A(5);
%     
%     n = w * w + x * x + y * y + z * z;
%     if n == 0 
%         s = 0;
%     else
%         s=2 / n;
%     end
%     wx = s * w * x; wy = s * w * y; wz = s * w * z;
%     xx = s * x * x; xy = s * x * y; xz = s * x * z;
%     yy = s * y * y; yz = s * y * z; zz = s * z * z;

    M=[[A(1),A(2),A(3)]',[A(4),A(5),A(6)]',[A(7),A(8),A(9)]'];
    M=inv(Mz)*M;
    roll=atan2(M(2,1),M(1,1));
    pitch=atan2(-M(3,1),sqrt(M(3,2)^2+M(3,3)^2));
    yaw=atan2(M(3,2),M(3,3));
    W=[roll,pitch,yaw]%abd/ad     flex/ext  sup/pro
    
    xx=M(:,1);
    yy=M(:,2);
    zz=M(:,3);
    plot3([0,xx(1)],[0,xx(2)],[0,xx(3)],'r');hold on
    plot3([0,yy(1)],[0,yy(2)],[0,yy(3)],'g');
    plot3([0,zz(1)],[0,zz(2)],[0,zz(3)],'b');
    axis([-1,1,-1,1,-1,1]);
    axis square
    hold off
    pause(0.05);
    if zeroflag==0;
        Mz=M;
        zeroflag=1;
    end
    
    if A(1)==3
        break;
    end
end

%% clean up
echoudp('off');
fclose(u);
delete(u);
close all;
