hx_connect('','');
hx_robot_info;
%%
command.ref_pos=zeros(13,1);
command.ref_vel=zeros(13,1);
command.gain_pos=zeros(13,1)*5;
command.gain_vel=zeros(13,1)*5;
%   and scalar fields specifying (as 1 or 0) which vectors to update:
command.ref_pos_enabled=1;
command.ref_vel_enabled=0;
command.gain_pos_enabled=0;
command.gain_vel_enabled=0;

mocap.nmocap=1;
mocap.time=0;
mocap.pos=[0 -0.3500 0.2000];
mocap.quat=[0 0 0 1];

%%% open udp
echoudp('on',4012);
u=udp('127.0.0.1', 4012, 'LocalPort', 4950);
fopen(u);

% control loop
zeroflag=0;
Mz=eye(3,3);
Pz=[0,0,0];

while(1)
    A = str2num(fscanf(u));
    mocap.pos=(A(11:13)-Pz)*0.0015;
    disp(A(1))
    %%% compute wrist
    M=[[A(2),A(3),A(4)]',[A(5),A(6),A(7)]',[A(8),A(9),A(10)]'];
      
    if zeroflag==0;
        Mz=M;
        Pz=A(11:13);
        zeroflag=1;
    end
    
    M=inv(Mz)*M;
    roll=atan2(M(2,1),M(1,1));
    pitch=atan2(-M(3,1),sqrt(M(3,2)^2+M(3,3)^2));
    yaw=atan2(M(3,2),M(3,3));
    W=[pitch,roll,yaw]%abd/ad  flex/ext  sup/pro
    
    %%% update hand
    if A(1)==3
        break;
    else
        command.ref_pos(5:12)=command.ref_pos(5:12)+A(1)*0.05*ones(8,1);
        command.ref_pos(1:3)=[-roll,-yaw,-pitch];
        command.ref_pos(4)=command.ref_pos(4)+A(1)*0.1;
        command.ref_pos(13)=command.ref_pos(13)+A(1)*0.1;
    end
    
%         mocap.pos(1)=mocap.pos(1)+0.01;
    

    
    hx_update(command);
    mj_set_mocap(mocap);

end

%% clean up
echoudp('off');
fclose(u);
delete(u);
hx_close;