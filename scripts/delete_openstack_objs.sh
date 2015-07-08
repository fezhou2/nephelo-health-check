for i in `neutron router-list| grep nephelo | cut -d\| -f2`; do
  PID=`neutron router-port-list $i | grep subnet| awk '{print \$8}'| cut -d\" -f2`
  if [ ! -z $PID ] 
  then
    neutron router-interface-delete  $i  $PID
  fi
done
for i in `neutron router-list| grep nephelo| cut -d\| -f2`;  do neutron router-delete $i; done
for i in `neutron subnet-list| grep nephelo| cut -d\| -f2`;  do neutron subnet-delete $i; done
for i in `neutron net-list| grep nephelo| cut -d\| -f2`;  do neutron net-delete $i; done
for i in `cinder list| grep nephelo| cut -d\| -f2`;  do cinder delete $i; done
for i in `glance image-list| grep nephelo| cut -d\| -f2`;  do glance image-delete $i; done
for i in `nova secgroup-list| grep nephelo| cut -d\| -f2`;  do nova secgroup-delete $i; done
